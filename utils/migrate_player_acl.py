from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from wiki_dasboard.components.access_control import _headings_by_line, _normalized_heading
from wiki_dasboard.components.metadata import split_frontmatter
from wiki_dasboard.config import cfg


FRONTMATTER_PATTERN = re.compile(
    r"\A---\r?\n(?P<metadata>.*?)\r?\n---(?P<separator>\r?\n|\Z)",
    re.DOTALL,
)
TOP_LEVEL_KEY_PATTERN = re.compile(r"^(?P<key>[A-Za-z_][\w-]*)\s*:")
LEGACY_PRIVATE_HEADINGS = {
    "ziele": "Ziele",
    "plot-hooks": "Plot-Hooks",
    "spielleiter": "Spielleiter",
    "kampfwerte": "Kampfwerte",
}
CHARACTER_PREFIXES = {
    "gn_": "gnodomir",
    "vs_": "vishuda",
    "hc_": "hector",
    "he_": "hector",
    "mc_": "marcus",
    "ny_": "nyssara",
}
SL_PREFIXES = ("sl_",)
MANAGED_KEYS = {"sichtbarkeit", "abschnitt_sichtbarkeit", "zugriff"}


class MigrationError(ValueError):
    pass


class _IndentedDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow, False)


def _normalized_value(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized.startswith("[[") and normalized.endswith("]]" ):
        normalized = normalized[2:-2].strip()
    return normalized.casefold()


def _values(value: Any) -> tuple[str, ...]:
    raw_values = value if isinstance(value, (list, tuple, set)) else (value,)
    return tuple(
        normalized
        for item in raw_values
        if (normalized := _normalized_value(item))
    )


def _campaign_ids(value: Any, aliases: Mapping[str, str]) -> set[str]:
    normalized_aliases = {
        _normalized_value(alias): _normalized_value(campaign_id)
        for alias, campaign_id in aliases.items()
    }
    return {
        normalized_aliases.get(campaign, campaign)
        for campaign in _values(value)
    }


def _parse_metadata(content: str) -> tuple[re.Match[str], dict[str, Any], str]:
    match = FRONTMATTER_PATTERN.match(content)
    if match is None:
        raise MigrationError("missing or malformed YAML frontmatter")
    try:
        metadata = yaml.safe_load(match.group("metadata")) or {}
    except yaml.YAMLError as error:
        raise MigrationError(f"invalid YAML frontmatter: {error}") from error
    if not isinstance(metadata, dict):
        raise MigrationError("frontmatter must be a mapping")
    body = content[match.end() :]
    return match, metadata, body


def _campaign_members_by_id(world_root: Path) -> dict[str, set[str]]:
    aliases = cfg.player_access.campaign_aliases
    profile_campaigns: dict[str, set[str]] = {}
    for path in world_root.rglob("*.md"):
        if "templates" in path.relative_to(world_root).parts:
            continue
        try:
            metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            continue
        character_id = _normalized_value(metadata.get("charakter_id"))
        if character_id:
            profile_campaigns[character_id] = _campaign_ids(
                metadata.get("kampagne"), aliases
            )

    campaign_members: dict[str, set[str]] = {}
    for character_id, campaigns in profile_campaigns.items():
        for campaign_id in campaigns:
            campaign_members.setdefault(campaign_id, set()).add(character_id)
    return campaign_members


def _legacy_character_grant(relative_path: Path) -> list[str]:
    matches = {
        character_id
        for part in relative_path.parts
        for prefix, character_id in CHARACTER_PREFIXES.items()
        if Path(part).stem.casefold().startswith(prefix)
    }
    if len(matches) > 1:
        raise MigrationError("path contains conflicting player-character prefixes")
    return sorted(matches)


def _migrate_document_grant(
    visibility: Any,
    metadata: Mapping[str, Any],
    relative_path: Path,
    campaign_members: Mapping[str, set[str]],
) -> tuple[list[str], str | None, Mapping[str, Any]]:
    section_rules: Mapping[str, Any] = {}
    gm_only: str | None = None

    if isinstance(visibility, dict):
        if "datei" not in visibility:
            raise MigrationError("legacy visibility mapping has no 'datei' grant")
        section_rules = visibility.get("abschnitte", {}) or {}
        visibility = visibility["datei"]

    if isinstance(visibility, str):
        normalized = _normalized_value(visibility)
        if normalized in {"dm", "spielleitung"}:
            return [], "spielleitung", section_rules
        if normalized in {"alle", "all", "public"}:
            return [], gm_only, section_rules
        if normalized == "kampagne":
            campaigns = _campaign_ids(metadata.get("kampagne"), cfg.player_access.campaign_aliases)
            characters = sorted(
                character_id
                for campaign_id in campaigns
                for character_id in campaign_members.get(campaign_id, set())
            )
            if not characters:
                raise MigrationError("campaign grant has no indexed character members")
            return characters, gm_only, section_rules
        return [normalized], gm_only, section_rules

    if isinstance(visibility, list):
        if any(not isinstance(value, str) or not value.strip() for value in visibility):
            raise MigrationError("visibility list contains a non-character value")
        return sorted(set(_values(visibility))), gm_only, section_rules

    raise MigrationError("unrecognized visibility metadata")


def _remove_managed_keys(metadata_text: str) -> str:
    retained: list[str] = []
    skipping = False
    for line in metadata_text.splitlines():
        if skipping:
            if not line.strip() or line[:1].isspace():
                continue
            skipping = False
        match = TOP_LEVEL_KEY_PATTERN.match(line)
        if match and match.group("key") in MANAGED_KEYS:
            skipping = True
            continue
        retained.append(line)
    return "\n".join(retained).rstrip()


def migrate_document_text(
    content: str,
    relative_path: Path,
    campaign_members: Mapping[str, set[str]],
) -> tuple[str, str]:
    match, metadata, body = _parse_metadata(content)
    if "sichtbarkeit" in metadata:
        visibility, gm_only, legacy_section_rules = _migrate_document_grant(
            metadata["sichtbarkeit"], metadata, relative_path, campaign_members
        )
    else:
        visibility = _legacy_character_grant(relative_path)
        gm_only = None
        legacy_section_rules = {}

    if not isinstance(legacy_section_rules, dict):
        raise MigrationError("legacy section visibility must be a mapping")
    section_rules = metadata.get("abschnitt_sichtbarkeit", {}) or {}
    if not isinstance(section_rules, dict):
        raise MigrationError("section visibility must be a mapping")
    merged_rules: dict[str, list[str]] = {}
    for heading, ids in legacy_section_rules.items():
        merged_rules[str(heading)] = list(_values(ids))
    for heading, ids in section_rules.items():
        merged_rules[str(heading)] = list(_values(ids))

    hidden_headings, _ = _headings_by_line(re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL))
    for normalized_heading, label in LEGACY_PRIVATE_HEADINGS.items():
        if normalized_heading in hidden_headings:
            merged_rules.setdefault(label, [])

    for heading in merged_rules:
        if _normalized_heading(heading) not in hidden_headings:
            raise MigrationError(f"section ACL target not found: {heading}")

    path_is_sl = any(
        Path(part).stem.casefold() == "spielleiter" for part in relative_path.parts
    ) or any(Path(part).stem.casefold().startswith(SL_PREFIXES) for part in relative_path.parts)
    if path_is_sl and gm_only is None and _normalized_value(metadata.get("status")) != "dm":
        gm_only = "spielleitung"
    existing_access = _normalized_value(metadata.get("zugriff"))
    if existing_access and existing_access != "spielleitung":
        raise MigrationError(f"unrecognized access override: {existing_access}")
    gm_only = gm_only or (existing_access or None)

    acl_metadata: dict[str, Any] = {"sichtbarkeit": visibility}
    if gm_only:
        acl_metadata["zugriff"] = gm_only
    if merged_rules:
        acl_metadata["abschnitt_sichtbarkeit"] = merged_rules

    acl_yaml = yaml.dump(
        acl_metadata,
        Dumper=_IndentedDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip()
    retained_metadata = _remove_managed_keys(match.group("metadata"))
    if retained_metadata:
        new_metadata = f"{retained_metadata}\n{acl_yaml}"
    else:
        new_metadata = acl_yaml
    migrated = (
        content[: match.start("metadata")]
        + new_metadata
        + content[match.end("metadata") :]
    )
    disposition = "game-master" if gm_only or _normalized_value(metadata.get("status")) == "dm" else (
        "character" if visibility else "public"
    )
    return migrated, disposition


def migrate_world(world_root: Path, *, apply: bool) -> dict[str, int]:
    campaign_members = _campaign_members_by_id(world_root)
    plans: list[tuple[Path, str, str]] = []
    errors: list[str] = []
    for path in sorted(world_root.rglob("*.md")):
        relative_path = path.relative_to(world_root)
        if any(ignored in part for part in relative_path.parts for ignored in cfg.navigation.ignored_paths):
            continue
        try:
            original = path.read_text(encoding="utf-8")
            migrated, disposition = migrate_document_text(
                original, relative_path, campaign_members
            )
        except (OSError, UnicodeError, MigrationError) as error:
            errors.append(f"{relative_path}: {error}")
            continue
        if migrated != original:
            plans.append((path, migrated, disposition))

    if errors:
        raise MigrationError("\n".join(errors))

    summary = {"changed": len(plans), "public": 0, "character": 0, "game-master": 0}
    for _, _, disposition in plans:
        summary[disposition] += 1
    if apply:
        for path, migrated, _ in plans:
            path.write_text(migrated, encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate World document ACL metadata")
    parser.add_argument("--apply", action="store_true", help="write migrated frontmatter")
    parser.add_argument("--world-root", type=Path, default=cfg.paths.world_dir)
    args = parser.parse_args()
    try:
        summary = migrate_world(args.world_root, apply=args.apply)
    except MigrationError as error:
        print(error, file=sys.stderr)
        return 1
    mode = "Applied" if args.apply else "Dry run"
    print(
        f"{mode}: {summary['changed']} files changed "
        f"({summary['public']} public, {summary['character']} character-restricted, "
        f"{summary['game-master']} GameMaster-only)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())