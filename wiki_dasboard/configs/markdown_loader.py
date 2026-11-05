from __future__ import annotations

import logging
from pathlib import Path
import re
import unicodedata

from wiki_dasboard.components.metadata import split_frontmatter
from wiki_dasboard.configs.user_config import (
    KampagneConfig,
    PlayerAccessConfig,
    PlayerAccessRegistryConfig,
)


LOGGER = logging.getLogger(__name__)
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
PLAYER_HEADING_PATTERN = re.compile(r"^#\s+(.+?)\s*$")
PLAYER_FIELD_PATTERN = re.compile(r"^\s*\*\*(?P<key>[^*]+)\*\*\s*:?\s*(?P<value>.*)$")
TABLE_ROW_PATTERN = re.compile(r"^\s*\|(?P<cells>.*)\|\s*$")
LIST_FIELDS = {"charaktere", "kampangen", "kampagnen"}
ROLE_VALUES = {
    "default": "Default",
    "player": "Player",
    "spieler": "Player",
    "gamemaster": "GameMaster",
    "game master": "GameMaster",
    "spielleiter": "GameMaster",
    "dm": "GameMaster",
}


def _plain_value(value: str) -> str:
    return WIKILINK_PATTERN.sub(lambda match: match.group(1).strip(), value).strip()


def _linked_values(value: str) -> tuple[str, ...]:
    values: list[str] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        links = tuple(
            match.group(1).strip() for match in WIKILINK_PATTERN.finditer(part)
        )
        values.extend(links or (_plain_value(part),))
    return tuple(values)


def _normalized_name(value: str) -> str:
    return " ".join(_plain_value(value).split()).casefold()


def _campaign_id(campaign_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", campaign_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
    return slug or "campaign"


def _read_markdown_body(path: Path) -> str:
    try:
        _, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        LOGGER.warning("Cannot read access config %s: %s", path, error)
        return ""
    return body


def _split_table_cells(row: str) -> list[str]:
    cells: list[str] = []
    cell: list[str] = []
    in_wikilink = False
    index = 0
    while index < len(row):
        if row.startswith("[[", index):
            in_wikilink = True
            cell.extend("[[")
            index += 2
        elif row.startswith("]]", index):
            in_wikilink = False
            cell.extend("]]" )
            index += 2
        elif row[index] == "|" and not in_wikilink:
            cells.append("".join(cell).strip())
            cell.clear()
            index += 1
        else:
            cell.append(row[index])
            index += 1
    cells.append("".join(cell).strip())
    return cells


def _parse_campaigns(path: Path) -> tuple[KampagneConfig, ...]:
    body = _read_markdown_body(path)
    header_indexes: dict[str, int] | None = None
    campaigns: list[KampagneConfig] = []

    for line in body.splitlines():
        match = TABLE_ROW_PATTERN.match(line)
        if match is None:
            continue
        cells = _split_table_cells(match.group("cells"))
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue

        if header_indexes is None:
            normalized_headers = [_normalized_name(cell) for cell in cells]
            campaign_column = next(
                (
                    index
                    for index, header in enumerate(normalized_headers)
                    if header.startswith(("kampag", "kampan")) and "name" in header
                ),
                None,
            )
            alias_column = next(
                (index for index, header in enumerate(normalized_headers) if "alias" in header),
                None,
            )
            if campaign_column is not None and alias_column is not None:
                header_indexes = {
                    "campaign_name": campaign_column,
                    "alias": alias_column,
                }
            continue

        if max(header_indexes.values()) >= len(cells):
            continue
        campaign_name = _plain_value(cells[header_indexes["campaign_name"]])
        alias = _plain_value(cells[header_indexes["alias"]])
        if not campaign_name:
            continue
        campaigns.append(
            KampagneConfig(
                campaign_id=_campaign_id(campaign_name),
                campaign_name=campaign_name,
                alias=alias or campaign_name,
            )
        )

    if not campaigns:
        LOGGER.warning("No campaign mappings found in %s", path)
    return tuple(campaigns)


def _parse_player_sections(path: Path) -> tuple[dict[str, object], ...]:
    body = _read_markdown_body(path)
    players: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    active_list_field: str | None = None

    def finish_player() -> None:
        if current is not None:
            players.append(current.copy())

    for line in body.splitlines():
        heading = PLAYER_HEADING_PATTERN.match(line)
        if heading:
            finish_player()
            current = {
                "name": _plain_value(heading.group(1)),
                "charaktere": [],
                "kampangen": [],
            }
            active_list_field = None
            continue
        if current is None:
            continue

        field_match = PLAYER_FIELD_PATTERN.match(line)
        if field_match:
            key = field_match.group("key").strip().rstrip(":").casefold()
            value = field_match.group("value").strip()
            if key in LIST_FIELDS:
                normalized_key = "kampangen" if key == "kampagnen" else key
                values = list(_linked_values(value)) if value else []
                current[normalized_key] = values
                active_list_field = normalized_key
            else:
                current[key] = _plain_value(value)
                active_list_field = None
            continue

        if active_list_field and line.strip().startswith(("- ", "* ")):
            values = _linked_values(line.strip()[2:].strip())
            current[active_list_field].extend(values)
        elif line.strip() and not line.lstrip().startswith(("---", "<!--")):
            active_list_field = None

    finish_player()
    return tuple(players)


def _character_id_index(world_root: Path) -> dict[str, set[str]]:
    names: dict[str, set[str]] = {}
    for path in world_root.rglob("*.md"):
        if any(part.casefold() in {"templates", "zugriffsrechte", ".obsidian"} for part in path.relative_to(world_root).parts):
            continue
        try:
            metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            continue
        character_id = str(metadata.get("charakter_id", "")).strip()
        if not character_id:
            continue
        aliases = {path.stem}
        for key in ("name", "charakter", "charakter_name"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                aliases.add(value.strip())
        for alias in aliases:
            names.setdefault(_normalized_name(alias), set()).add(character_id)
    return names


def load_player_access_registry(world_root: Path) -> PlayerAccessRegistryConfig:
    access_dir = world_root / "Zugriffsrechte"
    campaigns = _parse_campaigns(access_dir / "Kampangen Mappings.md")
    character_index = _character_id_index(world_root)
    campaigns_by_name: dict[str, KampagneConfig] = {}
    for campaign in campaigns:
        campaigns_by_name[_normalized_name(campaign.campaign_name)] = campaign
        campaigns_by_name[_normalized_name(campaign.alias)] = campaign

    players: list[PlayerAccessConfig] = []
    seen_user_names: set[str] = set()
    for section in _parse_player_sections(access_dir / "Spielerrechte.md"):
        name = str(section.get("name", "")).strip()
        user_name = _plain_value(str(section.get("username", ""))).strip()
        role_text = str(section.get("role", "")).strip().casefold()
        role = ROLE_VALUES.get(role_text)
        if not user_name or role is None:
            LOGGER.warning("Skipping incomplete player access entry %r", name)
            continue

        normalized_user_name = user_name.casefold()
        if normalized_user_name in seen_user_names:
            LOGGER.warning("Skipping duplicate player user_name %r", user_name)
            continue

        character_ids: list[str] = []
        for character_name in section.get("charaktere", []):
            matches = character_index.get(_normalized_name(str(character_name)), set())
            if len(matches) != 1:
                LOGGER.warning(
                    "Cannot resolve character %r for player %r",
                    character_name,
                    user_name,
                )
                continue
            character_ids.append(next(iter(matches)))

        player_campaigns: list[KampagneConfig] = []
        for campaign_name in section.get("kampangen", []):
            campaign = campaigns_by_name.get(_normalized_name(str(campaign_name)))
            if campaign is None:
                LOGGER.warning(
                    "Cannot resolve campaign %r for player %r",
                    campaign_name,
                    user_name,
                )
                continue
            if campaign not in player_campaigns:
                player_campaigns.append(campaign)

        players.append(
            PlayerAccessConfig(
                name=name,
                user_name=user_name,
                role=role,
                campaigns=tuple(player_campaigns),
                charakter=tuple(dict.fromkeys(character_ids)),
            )
        )
        seen_user_names.add(normalized_user_name)

    return PlayerAccessRegistryConfig(
        players=tuple(players),
        campaigns=campaigns,
    )