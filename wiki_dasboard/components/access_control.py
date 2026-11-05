from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
import re
from typing import Any

import streamlit as st

from wiki_dasboard.components.metadata import split_frontmatter
from wiki_dasboard.config import cfg

ATX_HEADING_PATTERN = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*#*\s*$")
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
SETEXT_HEADING_PATTERN = re.compile(r"^ {0,3}(=+|-+)\s*$")
GAME_MASTER_ONLY_HEADINGS = {
    "ziele",
    "plot-hooks",
    "spielleiter",
    "kampfwerte",
}
SECRET_INFORMATION_HEADING = "geheime informationen"


def _normalized_value(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized.startswith("[[") and normalized.endswith("]]" ):
        normalized = normalized[2:-2].strip()
    return normalized.casefold()


def _values(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    elif value is None:
        raw_values = ()
    else:
        raw_values = (value,)
    return tuple(
        normalized
        for item in raw_values
        if (normalized := _normalized_value(item))
    )


def _canonical_campaign_ids(
    value: Any, aliases: Mapping[str, str]
) -> set[str]:
    normalized_aliases = {
        _normalized_value(alias): _normalized_value(campaign_id)
        for alias, campaign_id in aliases.items()
    }
    return {
        normalized_aliases.get(campaign, campaign)
        for campaign in _values(value)
    }


def campaign_id_for_value(value: Any, aliases: Mapping[str, str]) -> str | None:
    campaign_ids = _canonical_campaign_ids(value, aliases)
    return next(iter(campaign_ids)) if len(campaign_ids) == 1 else None


def _user_character_ids(user: Any) -> set[str]:
    return set(_values(getattr(user, "character_ids", None)))


@st.cache_data(ttl=60)
def build_character_campaign_index(world_root: str) -> dict[str, tuple[str, ...]]:
    index: dict[str, tuple[str, ...]] = {}
    for path in Path(world_root).rglob("*.md"):
        try:
            metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            continue
        character_id = _normalized_value(metadata.get("charakter_id"))
        if character_id:
            index[character_id] = _values(metadata.get("kampagne"))
    return index


def campaigns_for_user(
    user: Any, world_root: str | Path
) -> tuple[tuple[str, str], ...]:
    aliases = dict(cfg.player_access.campaign_aliases)
    labels = dict(cfg.player_access.campaign_labels)
    configured_campaign_ids: set[str] = set()
    for campaign in getattr(user, "campaigns", ()) or ():
        campaign_id = _normalized_value(getattr(campaign, "campaign_id", ""))
        campaign_name = str(getattr(campaign, "campaign_name", "")).strip()
        alias = _normalized_value(getattr(campaign, "alias", ""))
        if campaign_id:
            configured_campaign_ids.add(campaign_id)
            if campaign_name:
                labels[campaign_id] = campaign_name
        if alias and campaign_id:
            aliases[alias] = campaign_id

    if configured_campaign_ids:
        campaign_ids = configured_campaign_ids
    else:
        index = build_character_campaign_index(str(world_root))
        campaign_ids = {
            campaign
            for character_id in _user_character_ids(user)
            for campaign in _canonical_campaign_ids(index.get(character_id, ()), aliases)
        }
    return tuple(
        (campaign_id, labels[campaign_id])
        for campaign_id in sorted(campaign_ids)
        if campaign_id in labels
    )


def _normalized_heading(value: str) -> str:
    value = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda match: match.group(2) or match.group(1),
        value,
    )
    value = re.sub(r"[*_`~]", "", value)
    return " ".join(value.split()).casefold()


def _headings_by_line(content: str) -> tuple[dict[str, list[int]], dict[int, tuple[int, str]]]:
    headings: dict[str, list[int]] = {}
    headings_by_line: dict[int, tuple[int, str]] = {}
    lines = content.splitlines()
    fence_character = None
    fence_length = 0

    for line_index, line in enumerate(lines):
        fence_match = FENCE_PATTERN.match(line)
        if fence_match:
            fence = fence_match.group(1)
            if fence_character is None:
                fence_character = fence[0]
                fence_length = len(fence)
            elif fence[0] == fence_character and len(fence) >= fence_length:
                fence_character = None
            continue
        if fence_character is not None:
            continue

        heading_match = ATX_HEADING_PATTERN.match(line)
        if heading_match:
            depth = len(heading_match.group(1))
            title = _normalized_heading(heading_match.group(2))
            headings.setdefault(title, []).append(line_index)
            headings_by_line[line_index] = (depth, title)
            continue

        if line_index > 0 and SETEXT_HEADING_PATTERN.match(line):
            title = _normalized_heading(lines[line_index - 1].strip())
            depth = 1 if line.lstrip().startswith("=") else 2
            headings.setdefault(title, []).append(line_index - 1)
            headings_by_line[line_index - 1] = (depth, title)

    return headings, headings_by_line


def _section_rules(
    section_visibility: Mapping[str, Any], body: str
) -> dict[str, set[str]] | None:
    configured_rules = section_visibility
    if not isinstance(configured_rules, dict):
        return None

    headings, _ = _headings_by_line(body)
    rules: dict[str, set[str]] = {}
    for heading, character_ids in configured_rules.items():
        normalized_heading = _normalized_heading(str(heading))
        characters = set(_values(character_ids))
        if (
            not normalized_heading
            or not headings.get(normalized_heading)
            or not isinstance(character_ids, list)
        ):
            return None
        rules[normalized_heading] = characters
    return rules


def section_acl_is_valid(section_visibility: Any, body: str) -> bool:
    if not isinstance(section_visibility, dict):
        return False
    return _section_rules(section_visibility, body) is not None


def filter_document_sections(content: str, user: Any) -> str:
    role = getattr(getattr(user, "role", None), "value", None)
    if role == "GameMaster":
        return content

    metadata, body = split_frontmatter(content)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    section_visibility = metadata.get("abschnitt_sichtbarkeit", {})
    if not isinstance(section_visibility, dict):
        return ""

    rules = _section_rules(section_visibility, body)
    if rules is None:
        return ""

    _, headings_by_line = _headings_by_line(body)
    characters = _user_character_ids(user)
    document_visibility = metadata.get("sichtbarkeit")
    document_characters = (
        set(_values(document_visibility))
        if isinstance(document_visibility, list)
        and all(isinstance(value, str) and value.strip() for value in document_visibility)
        else set()
    )
    hidden_depth: int | None = None
    filtered_lines: list[str] = []
    for line_index, line in enumerate(body.splitlines()):
        suppress_heading = False
        heading = headings_by_line.get(line_index)
        if heading is not None:
            depth, title = heading
            if hidden_depth is not None and depth <= hidden_depth:
                hidden_depth = None
            if title in GAME_MASTER_ONLY_HEADINGS:
                hidden_depth = depth
            elif title == SECRET_INFORMATION_HEADING:
                allowed_characters = rules.get(title, document_characters)
                if not (allowed_characters & characters):
                    hidden_depth = depth
                suppress_heading = True
            elif title in rules and not (rules[title] & characters):
                hidden_depth = depth
        if hidden_depth is None:
            if not suppress_heading:
                filtered_lines.append(line)

    return "\n".join(filtered_lines)


def can_view_document(
    file_path: str | Path,
    user: Any,
    world_root: str | Path,
    *,
    character_campaigns: Mapping[str, Iterable[str]] | None = None,
    campaign_aliases: Mapping[str, str] | None = None,
    campaign_id: str | None = None,
) -> bool:
    root = Path(world_root).resolve()
    path = Path(file_path).resolve()
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        return False

    if any(
        ignored in part
        for part in relative_path.parts
        for ignored in cfg.navigation.ignored_paths
    ):
        return False
    if not path.is_file() or path.suffix.casefold() != ".md":
        return False

    role = getattr(getattr(user, "role", None), "value", None)
    if role == "GameMaster":
        if campaign_id is None:
            return True
        try:
            metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            return False
        return _normalized_value(campaign_id) in _canonical_campaign_ids(
            metadata.get("kampagne"),
            campaign_aliases or cfg.player_access.campaign_aliases,
        )

    try:
        metadata, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return False
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)

    if (
        any(Path(part).stem.casefold() == "spielleiter" for part in relative_path.parts)
        or _normalized_value(metadata.get("status")) == "dm"
        or _normalized_value(metadata.get("zugriff")) == "spielleitung"
    ):
        return False

    visibility = metadata.get("sichtbarkeit")
    if not isinstance(visibility, list):
        return False
    if any(not isinstance(character_id, str) or not character_id.strip() for character_id in visibility):
        return False

    allowed = not visibility or bool(set(_values(visibility)) & _user_character_ids(user))
    if not allowed:
        return False
    if campaign_id is None:
        return True
    return _normalized_value(campaign_id) in _canonical_campaign_ids(
        metadata.get("kampagne"),
        campaign_aliases or cfg.player_access.campaign_aliases,
    )