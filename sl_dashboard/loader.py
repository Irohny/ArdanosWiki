from pathlib import Path
from dataclasses import dataclass
from typing import Any
import re

import yaml

from sl_dashboard.editor import get_bestiary_defenses
from sl_dashboard.models import (
    DashboardData,
    DashboardEncounter,
    EncounterCombatant,
    EncounterCondition,
    EncounterPreparation,
    DashboardLink,
    DashboardNpc,
    EncounterRuntime,
    DashboardScene,
    DashboardTool,
    SessionStatus,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "World" / "Spielleiter" / "OneShots"
BESTIARY_ROOT = REPO_ROOT / "World" / "Bestiarium"
IMAGE_EMBED_PATTERN = re.compile(r"!\[\[([^\]|]+)")
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
MARKDOWN_PROPERTY_PATTERN = re.compile(r"^\s*-\s+\*\*(.+?):\*\*\s*(.*)$")
SCENE_SECTION_FIELD_MAP = {
    "atmosphaere": "atmosphere",
    "atmosphere": "atmosphere",
    "ziel": "goal",
    "goal": "goal",
    "szenenbild": "summary",
    "summary": "summary",
    "zusammenfassung": "summary",
    "druck": "pressure",
    "pressure": "pressure",
    "was_auf_dem_spiel_steht": "stakes",
    "stakes": "stakes",
    "was_es_zu_entdecken_gibt": "discoveries",
    "discoveries": "discoveries",
    "wahrscheinliche_spieleraktionen": "likely_player_actions",
    "likely_player_actions": "likely_player_actions",
    "verdeckte_wahrheiten_fuer_die_sl": "hidden_truths",
    "hidden_truths": "hidden_truths",
}
PLACE_SECTION_FIELD_MAP = {
    "zusammenfassung": "summary",
    "summary": "summary",
    "einsatz": "reason",
    "relevanz": "reason",
    "reason": "reason",
    "atmosphaere": "atmosphere",
    "atmosphere": "atmosphere",
    "details": "details",
}
NPC_SECTION_FIELD_MAP = {
    "motivation": "motivation",
    "einsatz": "reason",
    "relevanz": "reason",
    "reason": "reason",
    "oeffentliche_zusammenfassung": "public_summary",
    "oeffentliche_notiz": "public_summary",
    "public_summary": "public_summary",
    "geheimnisse": "secrets",
}
MONSTER_SECTION_FIELD_MAP = {
    "zusammenfassung": "summary",
    "summary": "summary",
    "einsatz": "reason",
    "relevanz": "reason",
    "reason": "reason",
}
SESSION_SECTION_FIELD_MAP = {
    "aktuelles_ziel": "current_goal",
    "current_goal": "current_goal",
    "offene_faeden": "open_threads",
    "open_threads": "open_threads",
    "warnungen": "alerts",
    "alerts": "alerts",
    "notizen": "notes",
}
ENCOUNTER_STATE_FILE_NAMES = ("encounter_state.yaml", "encounter_state.yml")


@dataclass(frozen=True)
class SessionOption:
    key: str
    title: str
    path: Path


@dataclass(frozen=True)
class WorldRecordData:
    title: str = ""
    summary: str = ""
    image_file: str = ""
    properties: dict[str, str] | None = None


def _read_yaml_file(file_path: Path) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Ungueltige YAML-Struktur in {file_path}")
    return data


def _normalize_heading(value: str) -> str:
    replacements = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
    normalized = value.strip().casefold().translate(replacements)
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def _clean_markdown_inline(value: str) -> str:
    cleaned = re.sub(r"!\[\[([^\]]+)\]\]", "", value)
    cleaned = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda match: match.group(2) or match.group(1),
        cleaned,
    )
    cleaned = re.sub(r"[*_`#>]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" -")


def _split_frontmatter(content: str, file_path: Path) -> tuple[dict[str, Any], str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter_text = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            data = yaml.safe_load(frontmatter_text) or {}
            if not isinstance(data, dict):
                raise ValueError(f"Ungueltiges Frontmatter in {file_path}")
            return data, body

    raise ValueError(f"Nicht geschlossenes Frontmatter in {file_path}")


def _parse_markdown_sections(
    content: str,
    section_field_map: dict[str, str],
) -> dict[str, Any]:
    sections: dict[str, Any] = {}
    current_field: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_field
        if current_field is None:
            buffer = []
            return
        value = "\n".join(buffer).strip()
        if value:
            sections[current_field] = value
        buffer = []

    for line in content.splitlines():
        if line.startswith("## "):
            flush()
            heading = _normalize_heading(line[3:])
            current_field = section_field_map.get(heading)
            continue

        if current_field is not None:
            buffer.append(line)

    flush()
    return sections


def _extract_section_content(file_path: Path, heading: str) -> str:
    content = file_path.read_text(encoding="utf-8")
    if not heading:
        return content

    lines = content.splitlines()
    start_index = None
    heading_level = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == heading:
            start_index = index + 1
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            if heading_level == 0:
                heading_level = 6
            break

    if start_index is None:
        return content

    end_index = len(lines)
    for index in range(start_index, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("#"):
            current_level = len(stripped) - len(stripped.lstrip("#"))
            if current_level <= heading_level:
                end_index = index
                break
        elif stripped.startswith("### ") and heading.strip().startswith("### "):
            end_index = index
            break

    return "\n".join(lines[start_index:end_index])


def _read_world_content(file_path: str, source_heading: str = "") -> str:
    source_path = REPO_ROOT / file_path
    if not source_path.exists():
        return ""
    return _extract_section_content(source_path, source_heading)


def _extract_first_image(content: str) -> str:
    match = IMAGE_EMBED_PATTERN.search(content)
    if match is None:
        return ""
    return match.group(1).strip()


def _extract_title_from_content(
    content: str, fallback: str, source_heading: str = ""
) -> str:
    if source_heading:
        heading_title = _clean_markdown_inline(source_heading.lstrip("#").strip())
        if heading_title:
            return heading_title

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return _clean_markdown_inline(stripped.lstrip("#").strip())
        if stripped.startswith("**") and stripped.endswith("**"):
            return _clean_markdown_inline(stripped)
        break

    return fallback


def _extract_property_map(content: str) -> dict[str, str]:
    properties: dict[str, str] = {}
    for line in content.splitlines():
        match = MARKDOWN_PROPERTY_PATTERN.match(line)
        if match is None:
            continue
        properties[_normalize_heading(match.group(1))] = _clean_markdown_inline(
            match.group(2)
        )
    return properties


def _extract_first_text_block(content: str) -> str:
    blocks = re.split(r"\n\s*\n", content)
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if all(line.startswith(("#", "![[")) for line in lines):
            continue
        if all(MARKDOWN_PROPERTY_PATTERN.match(line) for line in lines):
            continue

        cleaned_lines: list[str] = []
        for line in lines:
            if line.startswith("![[") or line.startswith("#"):
                continue
            cleaned_lines.append(_clean_markdown_inline(line))

        cleaned_block = " ".join(line for line in cleaned_lines if line)
        if cleaned_block:
            return cleaned_block
    return ""


def _build_monster_summary(content: str, properties: dict[str, str]) -> str:
    merkmale = properties.get("merkmale", "")
    klasse = properties.get("klasse", "").replace("#", "")
    if klasse and merkmale:
        return f"{klasse} mit {merkmale}."
    if merkmale:
        return merkmale
    return _extract_first_text_block(content)


def _load_world_record(file_path: str, source_heading: str = "") -> WorldRecordData:
    if not file_path:
        return WorldRecordData(properties={})

    content = _read_world_content(file_path, source_heading)
    if not content:
        fallback_title = Path(file_path).stem
        return WorldRecordData(title=fallback_title, properties={})

    properties = _extract_property_map(content)
    summary = _extract_first_text_block(content)
    return WorldRecordData(
        title=_extract_title_from_content(
            content, Path(file_path).stem, source_heading
        ),
        summary=summary,
        image_file=_extract_first_image(content),
        properties=properties,
    )


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _read_markdown_file(
    file_path: Path,
    section_field_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(content, file_path)
    inline_properties = _extract_property_map(body)
    parsed_sections = _parse_markdown_sections(body, section_field_map or {})
    inferred_title = _extract_title_from_content(body, file_path.stem)
    inferred_fields: dict[str, Any] = {
        "id": file_path.stem,
        "title": inferred_title,
        "name": inferred_title,
        "nickname": inline_properties.get("rufname_beiname", ""),
    }
    return {**inline_properties, **inferred_fields, **frontmatter, **parsed_sections}


def _read_record_file(
    file_path: Path,
    section_field_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    if file_path.suffix.lower() == ".md":
        return _read_markdown_file(file_path, section_field_map=section_field_map)
    return _read_yaml_file(file_path)


def _load_records_by_id(
    directory: Path,
    *,
    section_field_map: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    if not directory.exists():
        return {}

    records: dict[str, dict[str, Any]] = {}
    file_paths = sorted(
        [*directory.glob("*.md"), *directory.glob("*.yaml"), *directory.glob("*.yml")]
    )
    for file_path in file_paths:
        record = _read_record_file(file_path, section_field_map=section_field_map)
        record.setdefault("source_file", _repo_relative_path(file_path))
        record_id = record.get("id")
        if not record_id:
            raise ValueError(f"Fehlende id in {file_path}")
        if str(record_id) in records:
            raise ValueError(f"Doppelte id {record_id} in {file_path}")
        records[str(record_id)] = record
    return records


def _resolve_records_dir(base_dir: Path, *names: str) -> Path:
    for name in names:
        candidate = base_dir / name
        if candidate.exists() and candidate.is_dir():
            return candidate

    lowered_names = {name.casefold() for name in names}
    for candidate in base_dir.iterdir() if base_dir.exists() else ():
        if candidate.is_dir() and candidate.name.casefold() in lowered_names:
            return candidate

    return base_dir / names[0]


def _repo_relative_path(file_path: Path) -> str:
    return str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")


def _as_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, list):
        return tuple(str(value) for value in values)
    if isinstance(values, tuple):
        return tuple(str(value) for value in values)
    return (str(values),)


def _extract_wiki_links_from_text(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, (list, tuple)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(_extract_wiki_links_from_text(item))
        return tuple(tokens)

    return tuple(match.strip() for match in WIKI_LINK_PATTERN.findall(str(value)))


def _collect_scene_link_tokens(
    scene_records: tuple[dict[str, Any], ...],
) -> tuple[str, ...]:
    ordered_tokens: list[str] = []
    seen_tokens: set[str] = set()

    for scene_record in scene_records:
        for field_name in (
            "summary",
            "goal",
            "pressure",
            "stakes",
            "discoveries",
            "likely_player_actions",
            "hidden_truths",
        ):
            for token in _extract_wiki_links_from_text(scene_record.get(field_name)):
                normalized = _normalize_heading(token)
                if not normalized or normalized in seen_tokens:
                    continue
                ordered_tokens.append(token)
                seen_tokens.add(normalized)

    return tuple(ordered_tokens)


def _is_monster_heading(value: str) -> bool:
    normalized = _normalize_heading(_clean_markdown_inline(value))
    return normalized in {"gegner", "monster", "feinde", "feindliche_kraefte"}


def _collect_scene_monster_tokens(
    scene_records: tuple[dict[str, Any], ...],
) -> tuple[str, ...]:
    ordered_tokens: list[str] = []
    seen_tokens: set[str] = set()

    for scene_record in scene_records:
        for field_name in (
            "summary",
            "goal",
            "pressure",
            "stakes",
            "discoveries",
            "likely_player_actions",
            "hidden_truths",
        ):
            value = scene_record.get(field_name)
            if value is None:
                continue

            lines: list[str] = []
            if isinstance(value, (list, tuple)):
                for item in value:
                    lines.extend(str(item).splitlines())
            else:
                lines = str(value).splitlines()

            in_monster_block = False
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                if stripped.startswith("### "):
                    in_monster_block = _is_monster_heading(stripped[4:])
                elif stripped.startswith("**") and stripped.endswith("**"):
                    in_monster_block = _is_monster_heading(stripped)

                if not in_monster_block:
                    continue

                for token in _extract_wiki_links_from_text(line):
                    normalized = _normalize_heading(token)
                    if not normalized or normalized in seen_tokens:
                        continue
                    ordered_tokens.append(token)
                    seen_tokens.add(normalized)

    return tuple(ordered_tokens)


def _record_lookup_keys(record: dict[str, Any]) -> tuple[str, ...]:
    keys: list[str] = []
    for field_name in ("id", "title", "name"):
        field_value = str(record.get(field_name, "")).strip()
        if field_value:
            keys.append(_normalize_heading(field_value))

    for field_name in ("world_file", "source_file"):
        file_value = str(record.get(field_name, "")).strip()
        if not file_value:
            continue
        keys.append(_normalize_heading(Path(file_value).stem))

    source_heading = str(record.get("source_heading", "")).strip()
    if source_heading:
        keys.append(_normalize_heading(source_heading.lstrip("# ")))

    deduped_keys: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if not key or key in seen:
            continue
        deduped_keys.append(key)
        seen.add(key)
    return tuple(deduped_keys)


def _build_record_lookup(records_by_id: dict[str, dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for record_id, record in records_by_id.items():
        for key in _record_lookup_keys(record):
            lookup.setdefault(key, record_id)
    return lookup


def _collect_linked_record_ids(
    scene_records: tuple[dict[str, Any], ...],
    records_by_id: dict[str, dict[str, Any]],
) -> tuple[str, ...]:
    if not records_by_id:
        return ()

    lookup = _build_record_lookup(records_by_id)
    ordered_ids: list[str] = []
    seen_ids: set[str] = set()

    for scene_record in scene_records:
        for field_name in (
            "summary",
            "goal",
            "pressure",
            "stakes",
            "discoveries",
            "likely_player_actions",
            "hidden_truths",
        ):
            for token in _extract_wiki_links_from_text(scene_record.get(field_name)):
                record_id = lookup.get(_normalize_heading(token))
                if record_id is None or record_id in seen_ids:
                    continue
                ordered_ids.append(record_id)
                seen_ids.add(record_id)

    return tuple(ordered_ids)


def _load_world_monster_records(
    scene_records: tuple[dict[str, Any], ...],
    existing_records: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    linked_tokens = _collect_scene_link_tokens(scene_records)
    monster_tokens = _collect_scene_monster_tokens(scene_records)
    if not linked_tokens and not monster_tokens:
        return {}

    existing_lookup = _build_record_lookup(existing_records)
    bestiary_lookup: dict[str, dict[str, Any]] = {}

    if BESTIARY_ROOT.exists():
        for file_path in sorted(BESTIARY_ROOT.glob("*.md")):
            relative_path = _repo_relative_path(file_path)
            world_record = _load_world_record(relative_path)
            title = world_record.title or file_path.stem
            record = {
                "id": f"world-monster-{_normalize_heading(file_path.stem)}",
                "title": title,
                "name": title,
                "context": "Monster",
                "world_file": relative_path,
                "source_file": relative_path,
                "summary": world_record.summary,
                "image": world_record.image_file,
            }
            for key in _record_lookup_keys(record):
                bestiary_lookup.setdefault(key, record)

    candidate_tokens: list[str] = []
    seen_candidates: set[str] = set()
    for token in linked_tokens:
        normalized_token = _normalize_heading(token)
        if (
            normalized_token
            and normalized_token in bestiary_lookup
            and normalized_token not in seen_candidates
        ):
            candidate_tokens.append(token)
            seen_candidates.add(normalized_token)
    for token in monster_tokens:
        normalized_token = _normalize_heading(token)
        if not normalized_token or normalized_token in seen_candidates:
            continue
        candidate_tokens.append(token)
        seen_candidates.add(normalized_token)

    supplemental_records: dict[str, dict[str, Any]] = {}
    for token in candidate_tokens:
        normalized_token = _normalize_heading(token)
        if not normalized_token or normalized_token in existing_lookup:
            continue

        matched_record = bestiary_lookup.get(normalized_token)
        if matched_record is not None:
            supplemental_records.setdefault(str(matched_record["id"]), matched_record)
            continue

        synthetic_id = f"scene-monster-{normalized_token}"
        supplemental_records.setdefault(
            synthetic_id,
            {
                "id": synthetic_id,
                "title": token,
                "name": token,
                "context": "Monster",
                "reason": "In der aktiven Szene verlinkt.",
            },
        )

    return supplemental_records


def _build_scene(record: dict[str, Any]) -> DashboardScene:
    return DashboardScene(
        title=str(record.get("title", "Unbenannte Szene")),
        status=str(record.get("status", "offen")),
        summary=str(record.get("summary", "")),
        location=str(record.get("location", "")),
        id=_first_non_empty(
            str(record.get("id", "")),
            str(record.get("title", "")),
        ),
        encounter=record.get("encounter"),
        source_file=str(record.get("source_file", "")),
        source_heading=str(record.get("source_heading", "")),
        image_files=_as_tuple(record.get("image_files")),
        goal=str(record.get("goal", "")),
        atmosphere=str(record.get("atmosphere", "")),
        pressure=str(record.get("pressure", "")),
        stakes=_as_tuple(record.get("stakes")),
        discoveries=_as_tuple(record.get("discoveries")),
        likely_player_actions=_as_tuple(record.get("likely_player_actions")),
        hidden_truths=_as_tuple(record.get("hidden_truths")),
    )


def _resolve_encounter_state_file(base_dir: Path) -> Path | None:
    for name in ENCOUNTER_STATE_FILE_NAMES:
        candidate = base_dir / name
        if candidate.exists():
            return candidate
    return None


def _load_encounter_state(base_dir: Path) -> dict[str, Any]:
    encounter_state_file = _resolve_encounter_state_file(base_dir)
    if encounter_state_file is None:
        return {}
    return _read_yaml_file(encounter_state_file)


def _build_encounter_condition(record: Any) -> EncounterCondition:
    if not isinstance(record, dict):
        return EncounterCondition(name=str(record).strip())

    return EncounterCondition(
        name=str(record.get("name", "")).strip(),
        duration=str(record.get("duration", "")).strip(),
        source=str(record.get("source", "")).strip(),
        notes=str(record.get("notes", "")).strip(),
    )


def _build_encounter_combatant(record: Any) -> EncounterCombatant:
    if not isinstance(record, dict):
        raise ValueError("Encounter-Combatant muss ein Dictionary sein.")

    source_type = str(record.get("source_type", "")).strip()
    source_key = str(record.get("source_key", "")).strip()
    conditions = tuple(
        _build_encounter_condition(condition)
        for condition in record.get("conditions", ()) or ()
    )
    bestiary_defenses = (
        get_bestiary_defenses(source_key)
        if source_type == "bestiary" and source_key
        else {
            "immunities": (),
            "resistances": (),
            "weaknesses": (),
        }
    )
    immunities = _as_tuple(record.get("immunities")) or bestiary_defenses["immunities"]
    resistances = _as_tuple(record.get("resistances")) or bestiary_defenses["resistances"]
    weaknesses = _as_tuple(record.get("weaknesses")) or bestiary_defenses["weaknesses"]

    return EncounterCombatant(
        id=str(record.get("id", "")).strip(),
        name=str(record.get("name", "")).strip(),
        side=str(record.get("side", "")).strip(),
        source_type=source_type,
        source_key=source_key,
        max_hp=record.get("max_hp") if isinstance(record.get("max_hp"), int) else None,
        current_hp=(
            record.get("current_hp")
            if isinstance(record.get("current_hp"), int)
            else None
        ),
        initiative=(
            record.get("initiative")
            if isinstance(record.get("initiative"), int)
            else None
        ),
        armor_class=(
            record.get("armor_class")
            if isinstance(record.get("armor_class"), int)
            else None
        ),
        immunities=immunities,
        resistances=resistances,
        weaknesses=weaknesses,
        conditions=conditions,
        notes=str(record.get("notes", "")).strip(),
    )


def _build_encounter_preparation(record: Any) -> EncounterPreparation:
    if not isinstance(record, dict):
        return EncounterPreparation()

    return EncounterPreparation(
        target_difficulty=str(record.get("target_difficulty", "")).strip(),
        predicted_difficulty=str(record.get("predicted_difficulty", "")).strip(),
        monster_source_keys=_as_tuple(record.get("monster_source_keys")),
        analysis_summary=str(record.get("analysis_summary", "")).strip(),
        analysis_notes=_as_tuple(record.get("analysis_notes")),
    )


def _build_encounter_runtime(record: Any) -> EncounterRuntime:
    if not isinstance(record, dict):
        return EncounterRuntime()

    combatants = tuple(
        _build_encounter_combatant(combatant)
        for combatant in record.get("combatants", ()) or ()
    )

    round_number = record.get("round_number")
    if not isinstance(round_number, int) or round_number < 1:
        round_number = 1

    return EncounterRuntime(
        round_number=round_number,
        active_combatant_id=str(record.get("active_combatant_id", "")).strip(),
        combatants=combatants,
    )


def _build_dashboard_encounter(scene_id: str, record: Any) -> DashboardEncounter | None:
    if not isinstance(record, dict) or not record:
        return None

    return DashboardEncounter(
        scene_id=scene_id,
        status=str(record.get("status", "draft")).strip() or "draft",
        preparation=_build_encounter_preparation(record.get("preparation")),
        runtime=_build_encounter_runtime(record.get("runtime")),
        notes=_as_tuple(record.get("notes")),
    )


def _build_link(record: dict[str, Any]) -> DashboardLink:
    source_file = str(record.get("world_file", record.get("source_file", "")))
    source_heading = str(record.get("source_heading", ""))
    world_record = _load_world_record(source_file, source_heading)
    properties = world_record.properties or {}
    context = str(record.get("context", "Link"))

    if context.casefold() == "monster":
        reason = _first_non_empty(
            str(record.get("species", "")),
            str(record.get("race", "")),
            str(record.get("volk", "")),
            properties.get("volk", ""),
            properties.get("rasse", ""),
            str(record.get("reason", "")),
            str(record.get("summary", "")),
        )
        if not reason:
            reason = _build_monster_summary(
                _read_world_content(source_file, source_heading), properties
            )
    else:
        reason = str(record.get("reason", record.get("summary", "")))
        if not reason:
            reason = world_record.summary

    return DashboardLink(
        title=_first_non_empty(
            str(record.get("title", "")),
            str(record.get("name", "")),
            world_record.title,
            "Unbenannter Eintrag",
        ),
        context=context,
        reason=reason,
        source_file=source_file,
        source_heading=source_heading,
        image_file=_first_non_empty(
            str(record.get("image", "")),
            str(record.get("handout_file", "")),
            world_record.image_file,
        ),
    )


def _build_npc(record: dict[str, Any]) -> DashboardNpc:
    source_file = str(record.get("world_file", record.get("source_file", "")))
    source_heading = str(record.get("source_heading", ""))
    world_record = _load_world_record(source_file, source_heading)
    properties = world_record.properties or {}

    title = _first_non_empty(
        str(record.get("titel_amt", "")),
        properties.get("titel_amt", ""),
        properties.get("titel", ""),
        properties.get("amt", ""),
    )
    species = _first_non_empty(
        str(record.get("spezies_volk", "")),
        properties.get("spezies_volk", ""),
        properties.get("rasse", ""),
        properties.get("volk", ""),
    )

    motivation = _first_non_empty(
        str(record.get("motivation", "")),
        properties.get("motiv", ""),
        properties.get("motivation", ""),
        properties.get("konflikt", ""),
        properties.get("wissen", ""),
        properties.get("geheimnis", ""),
    )

    return DashboardNpc(
        name=_first_non_empty(
            str(record.get("name", "")),
            world_record.title,
            "Unbenannter NSC",
        ),
        role=_first_non_empty(
            str(record.get("role", "")),
            title,
            properties.get("rolle", ""),
            properties.get("beruf", ""),
            properties.get("titel", ""),
        ),
        motivation=motivation,
        tension=str(record.get("tension", "")),
        species=species,
        location=_first_non_empty(
            str(record.get("location", "")),
            str(record.get("ort", "")),
            properties.get("ort", ""),
            properties.get("verknuepfte_orte", ""),
            properties.get("herkunft", ""),
        ),
        title=title,
        voice=_first_non_empty(
            str(record.get("voice", "")),
            properties.get("auftreten", ""),
        ),
        reason=_first_non_empty(
            str(record.get("reason", "")),
            str(record.get("public_summary", "")),
            properties.get("eindruck", ""),
            properties.get("beziehung", ""),
            properties.get("sl_hinweis", ""),
            properties.get("rolle_nach_tod", ""),
            motivation,
            world_record.summary,
        ),
        source_file=source_file,
        source_heading=source_heading,
        image_file=_first_non_empty(
            str(record.get("portrait", "")),
            str(record.get("image", "")),
            world_record.image_file,
        ),
    )


def _build_tools() -> tuple[DashboardTool, ...]:
    return (
        DashboardTool(
            title="Encounter-Rechner",
            description="Kampfschwierigkeit, Volatilitaet und Ressourcenlast schnell pruefen.",
            status="bestehend",
            emphasis="hoch",
        ),
        DashboardTool(
            title="NSC-Schnellansicht",
            description="Kurzprofil mit Motivation, Haltung und Stimme.",
            status="geplant",
        ),
        DashboardTool(
            title="Sitzungsnotizen",
            description="Private Notizen fuer Verlauf, Improvisation und Folgen.",
            status="geplant",
        ),
    )


def _resolve_session_dir(session_dir: Path | None = None) -> Path:
    if session_dir is not None:
        return session_dir

    candidates = sorted(path for path in DATA_ROOT.iterdir() if path.is_dir())
    if not candidates:
        raise FileNotFoundError("Keine Session-Daten unter sl_dashboard/data gefunden.")
    return candidates[0]


def _resolve_session_file(base_dir: Path) -> Path:
    for name in ("session.md", "session.yaml", "session.yml"):
        candidate = base_dir / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Keine Session-Datei in {base_dir} gefunden.")


def list_available_sessions() -> tuple[SessionOption, ...]:
    if not DATA_ROOT.exists():
        return ()

    session_options: list[SessionOption] = []
    for path in sorted(
        candidate for candidate in DATA_ROOT.iterdir() if candidate.is_dir()
    ):
        try:
            session_file = _resolve_session_file(path)
        except FileNotFoundError:
            continue

        session_record = _read_record_file(
            session_file, section_field_map=SESSION_SECTION_FIELD_MAP
        )
        session_options.append(
            SessionOption(
                key=path.name,
                title=str(session_record.get("session_title", path.name)),
                path=path,
            )
        )

    return tuple(session_options)


def get_session_dir_by_key(session_key: str) -> Path:
    for session_option in list_available_sessions():
        if session_option.key == session_key:
            return session_option.path
    raise FileNotFoundError(f"Session {session_key} wurde nicht gefunden.")


def load_dashboard_data(session_dir: Path | None = None) -> DashboardData:
    base_dir = _resolve_session_dir(session_dir)
    session_record = _read_record_file(
        _resolve_session_file(base_dir),
        section_field_map=SESSION_SECTION_FIELD_MAP,
    )
    encounter_state = _load_encounter_state(base_dir)
    encounters_by_scene_id = encounter_state.get("scenes", {})
    if not isinstance(encounters_by_scene_id, dict):
        raise ValueError(f"Ungueltiger Encounter-State in {base_dir}")

    scenes_by_id = _load_records_by_id(
        _resolve_records_dir(base_dir, "scenes", "Scenes"),
        section_field_map=SCENE_SECTION_FIELD_MAP,
    )
    places_by_id = _load_records_by_id(
        _resolve_records_dir(base_dir, "places", "Places"),
        section_field_map=PLACE_SECTION_FIELD_MAP,
    )
    npcs_by_id = _load_records_by_id(
        _resolve_records_dir(base_dir, "npcs", "NPCs"),
        section_field_map=NPC_SECTION_FIELD_MAP,
    )
    monsters_by_id = _load_records_by_id(
        _resolve_records_dir(base_dir, "monsters", "Monsters"),
        section_field_map=MONSTER_SECTION_FIELD_MAP,
    )

    current_scene_id = str(session_record.get("current_scene", ""))
    if current_scene_id not in scenes_by_id:
        raise ValueError(f"Aktuelle Szene {current_scene_id} wurde nicht gefunden.")

    scene_ids = _as_tuple(session_record.get("scene_ids"))
    ordered_scene_ids = scene_ids or tuple(scenes_by_id.keys())
    ordered_scene_records = tuple(
        scenes_by_id[scene_id]
        for scene_id in ordered_scene_ids
        if scene_id in scenes_by_id
    )
    monsters_by_id = {
        **monsters_by_id,
        **_load_world_monster_records(ordered_scene_records, monsters_by_id),
    }
    current_scene = _build_scene(
        {
            **scenes_by_id[current_scene_id],
            "encounter": _build_dashboard_encounter(
                current_scene_id,
                encounters_by_scene_id.get(current_scene_id),
            ),
        }
    )
    next_scenes = tuple(
        _build_scene(
            {
                **scenes_by_id[scene_id],
                "encounter": _build_dashboard_encounter(
                    scene_id,
                    encounters_by_scene_id.get(scene_id),
                ),
            }
        )
        for scene_id in ordered_scene_ids
        if scene_id != current_scene_id and scene_id in scenes_by_id
    )

    place_ids = _collect_linked_record_ids(ordered_scene_records, places_by_id)
    monster_ids = _collect_linked_record_ids(ordered_scene_records, monsters_by_id)
    npc_ids = _collect_linked_record_ids(ordered_scene_records, npcs_by_id)

    quick_links = tuple(
        _build_link({**places_by_id[place_id], "context": "Ort"})
        for place_id in place_ids
        if place_id in places_by_id
    ) + tuple(
        _build_link({**monsters_by_id[monster_id], "context": "Monster"})
        for monster_id in monster_ids
        if monster_id in monsters_by_id
    )

    npcs = tuple(
        _build_npc(npcs_by_id[npc_id]) for npc_id in npc_ids if npc_id in npcs_by_id
    )

    status = SessionStatus(
        session_title=str(session_record.get("session_title", "SL-Session")),
        in_game_date=str(session_record.get("in_game_date", "")),
        region=str(session_record.get("region", "")),
        current_scene=str(current_scene.title),
        current_goal=str(session_record.get("current_goal", "")),
        pacing=str(session_record.get("pacing", "")),
        open_threads=_as_tuple(session_record.get("open_threads")),
    )

    return DashboardData(
        status=status,
        current_scene=current_scene,
        next_scenes=next_scenes,
        npcs=npcs,
        quick_links=quick_links,
        tools=_build_tools(),
        notes=_as_tuple(session_record.get("notes")),
        alerts=_as_tuple(session_record.get("alerts")),
    )
