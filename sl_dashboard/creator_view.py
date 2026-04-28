from pathlib import Path
import re

import streamlit as st
import yaml

from components.monster_creator import render_monster_creator_view
from sl_dashboard.components.markdown import render_wiki_markdown
from sl_dashboard.editor import (
    add_bestiary_combatant_to_encounter,
    add_player_combatant_to_encounter,
    create_npc,
    create_scene,
    create_session,
    get_bestiary_armor_class,
    get_scene_id,
    link_bestiary_monster_to_scene,
    list_bestiary_monsters,
    read_scene_encounter_record,
    read_record_content,
    read_session_content,
    list_session_records,
    update_encounter_combatant,
    update_scene_encounter_record,
    update_record_content,
    update_session_content,
)


FLASH_MESSAGE_KEY = "sl_creator_flash_message"
WORKSHOP_SECTION_KEY = "sl_creator_active_section"
WORKSHOP_SECTION_OVERVIEW = 0
WORKSHOP_SECTION_SCENES = 1
WORKSHOP_SECTION_NPCS = 2
WORKSHOP_SECTION_MONSTERS = 3
WORKSHOP_SECTION_COMBAT = 4
WORKSHOP_SECTIONS = {
    WORKSHOP_SECTION_OVERVIEW: "Uebersicht",
    WORKSHOP_SECTION_SCENES: "Szenen",
    WORKSHOP_SECTION_NPCS: "NSC",
    WORKSHOP_SECTION_MONSTERS: "Monster",
    WORKSHOP_SECTION_COMBAT: "Combat",
}
MARKDOWN_PROPERTY_LINE_PATTERN = re.compile(r"^\s*-\s+\*\*(.+?):\*\*\s*(.*)$")
SCENE_STATUS_OPTIONS = ("aktiv", "vorbereitet", "optional", "spaeter")
SCENE_FRONTMATTER_FIELDS = {
    "id",
    "title",
    "status",
    "location",
    "source_file",
    "source_heading",
    "image_files",
}
SESSION_FRONTMATTER_FIELDS = {
    "session_title",
    "in_game_date",
    "region",
    "current_scene",
    "scene_ids",
}
NPC_EXPANDED_TEXT_FIELDS = {
    "Bekannt für",
    "Bindungen",
    "Ideale",
    "Merkmale",
    "Sprachen",
    "Tags",
    "Verknüpfte NPCs",
    "Verknüpfte Orte",
}
NPC_TEMPLATE_SECTION_FIELDS = (
    ("Beschreibung und Auftreten", "description", 140),
    ("Rolle und Beziehungen", "role_relationships", 140),
    ("Ziele", "goals", 120),
    ("Plot-Hooks", "plot_hooks", 120),
    ("Geheime Informationen", "secret_information", 120),
    ("Kampfwerte", "combat_values", 120),
)
SCENE_TEMPLATE_SECTION_FIELDS = (
    ("Atmosphaere", "Atmosphäre", "atmosphere", 110),
    ("Ziel", "Ziel", "goal", 110),
    ("Szenenbild", "Szenenbild", "summary", 150),
)
SESSION_TEMPLATE_SECTION_FIELDS = (
    ("Aktuelles Ziel", "current_goal", 150),
    ("Warnungen", "alerts", 150),
)


def _split_frontmatter(content: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", content, re.DOTALL)
    if match is None:
        return ("", content)
    return (match.group(1).strip(), match.group(2).strip())


def _render_preview_panel(content: str) -> None:
    frontmatter, body = _split_frontmatter(content)
    with st.container(border=True):
        st.markdown("**Vorschau**")
        if frontmatter:
            st.caption("Frontmatter")
            st.code(frontmatter, language="yaml")
        if body:
            render_wiki_markdown(body)
        elif not frontmatter:
            st.caption("Keine Vorschau verfuegbar.")


def _render_editor_with_preview(
    *,
    state_prefix: str,
    selection_key: str,
    content: str,
    height: int,
) -> str:
    content_state_key = f"{state_prefix}::content"
    loaded_state_key = f"{state_prefix}::loaded"

    if st.session_state.get(loaded_state_key) != selection_key:
        st.session_state[content_state_key] = content
        st.session_state[loaded_state_key] = selection_key

    left_col, right_col = st.columns((1, 1), gap="large")
    with left_col:
        st.text_area(
            "Markdown-Inhalt",
            key=content_state_key,
            height=height,
        )
    with right_col:
        _render_preview_panel(st.session_state.get(content_state_key, content))

    return str(st.session_state.get(content_state_key, content))


def _parse_frontmatter_dict(content: str) -> tuple[dict, str]:
    frontmatter_text, body = _split_frontmatter(content)
    if not frontmatter_text:
        return ({}, body)

    parsed_frontmatter = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(parsed_frontmatter, dict):
        return ({}, body)
    return (parsed_frontmatter, body)


def _compose_frontmatter_content(frontmatter: dict, body: str) -> str:
    dumped_frontmatter = yaml.safe_dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
    ).strip()
    if body.strip():
        return f"---\n{dumped_frontmatter}\n---\n\n{body.strip()}\n"
    return f"---\n{dumped_frontmatter}\n---\n"


def _sync_first_heading(body: str, title: str) -> str:
    normalized_title = title.strip()
    normalized_body = body.strip()
    if not normalized_title:
        return normalized_body

    heading = f"# {normalized_title}"
    if not normalized_body:
        return heading
    if re.search(r"^#\s+.+$", normalized_body, flags=re.MULTILINE):
        return re.sub(
            r"^#\s+.+$",
            heading,
            normalized_body,
            count=1,
            flags=re.MULTILINE,
        )
    return f"{heading}\n\n{normalized_body}"


def _scene_status_options(current_status: str) -> tuple[str, ...]:
    normalized_status = current_status.strip()
    if not normalized_status or normalized_status in SCENE_STATUS_OPTIONS:
        return SCENE_STATUS_OPTIONS
    return (normalized_status, *SCENE_STATUS_OPTIONS)


def _build_state_token(label: str, index: int) -> str:
    normalized_label = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
    return f"{index}-{normalized_label or 'field'}"


def _normalize_template_heading(value: str) -> str:
    replacements = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
    normalized = value.strip().casefold().translate(replacements)
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _parse_markdown_property_block(
    content: str,
) -> tuple[str, tuple[tuple[str, str], ...], str]:
    lines = content.splitlines()
    cursor = 0
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1

    heading = ""
    if cursor < len(lines) and lines[cursor].startswith("# "):
        heading = lines[cursor][2:].strip()
        cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1

    properties: list[tuple[str, str]] = []
    body_start = cursor
    while body_start < len(lines):
        line = lines[body_start]
        if not line.strip():
            body_start += 1
            continue
        match = MARKDOWN_PROPERTY_LINE_PATTERN.match(line)
        if match is None:
            break
        properties.append((match.group(1).strip(), match.group(2).strip()))
        body_start += 1

    body = "\n".join(lines[body_start:]).strip()
    return (heading, tuple(properties), body)


def _strip_html_comments(content: str) -> str:
    return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()


def _parse_npc_template_sections(content: str) -> tuple[dict[str, str], str]:
    sections = {
        state_key: "" for _heading, state_key, _height in NPC_TEMPLATE_SECTION_FIELDS
    }
    heading_to_state_key = {
        heading: state_key
        for heading, state_key, _height in NPC_TEMPLATE_SECTION_FIELDS
    }
    extra_chunks: list[str] = []
    current_heading: str | None = None
    current_state_key: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_heading, current_state_key
        raw_text = "\n".join(buffer).strip()
        cleaned_text = _strip_html_comments(raw_text)
        if current_state_key is not None:
            if cleaned_text:
                sections[current_state_key] = cleaned_text
        elif current_heading is not None:
            if cleaned_text:
                extra_chunks.append(f"## {current_heading}\n\n{cleaned_text}")
        elif cleaned_text:
            extra_chunks.append(cleaned_text)
        buffer = []

    for line in content.splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_state_key = heading_to_state_key.get(current_heading)
            continue
        buffer.append(line)

    flush()
    extra_body = "\n\n".join(chunk for chunk in extra_chunks if chunk.strip()).strip()
    return (sections, extra_body)


def _parse_scene_template_sections(content: str) -> tuple[dict[str, str], str]:
    sections = {
        state_key: ""
        for _display_label, _markdown_heading, state_key, _height in SCENE_TEMPLATE_SECTION_FIELDS
    }
    heading_to_state_key = {
        _normalize_template_heading(markdown_heading): state_key
        for _display_label, markdown_heading, state_key, _height in SCENE_TEMPLATE_SECTION_FIELDS
    }
    extra_chunks: list[str] = []
    current_heading: str | None = None
    current_state_key: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_heading, current_state_key
        raw_text = "\n".join(buffer).strip()
        cleaned_text = _strip_html_comments(raw_text)
        if current_state_key is not None:
            if cleaned_text:
                sections[current_state_key] = cleaned_text
        elif current_heading is not None:
            if cleaned_text:
                extra_chunks.append(f"## {current_heading}\n\n{cleaned_text}")
        elif cleaned_text:
            extra_chunks.append(cleaned_text)
        buffer = []

    for line in content.splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_state_key = heading_to_state_key.get(
                _normalize_template_heading(current_heading)
            )
            continue
        buffer.append(line)

    flush()
    extra_body = "\n\n".join(chunk for chunk in extra_chunks if chunk.strip()).strip()
    return (sections, extra_body)


def _parse_session_template_sections(content: str) -> tuple[dict[str, str], str]:
    sections = {
        state_key: "" for _heading, state_key, _height in SESSION_TEMPLATE_SECTION_FIELDS
    }
    heading_to_state_key = {
        _normalize_template_heading(heading): state_key
        for heading, state_key, _height in SESSION_TEMPLATE_SECTION_FIELDS
    }
    extra_chunks: list[str] = []
    current_heading: str | None = None
    current_state_key: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_heading, current_state_key
        raw_text = "\n".join(buffer).strip()
        cleaned_text = _strip_html_comments(raw_text)
        if current_state_key is not None:
            if cleaned_text:
                sections[current_state_key] = cleaned_text
        elif current_heading is not None:
            if cleaned_text:
                extra_chunks.append(f"## {current_heading}\n\n{cleaned_text}")
        elif cleaned_text:
            extra_chunks.append(cleaned_text)
        buffer = []

    for line in content.splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_state_key = heading_to_state_key.get(
                _normalize_template_heading(current_heading)
            )
            continue
        buffer.append(line)

    flush()
    extra_body = "\n\n".join(chunk for chunk in extra_chunks if chunk.strip()).strip()
    return (sections, extra_body)


def _compose_markdown_property_content(
    *,
    heading: str,
    properties: tuple[tuple[str, str], ...],
    body: str,
) -> str:
    lines: list[str] = []
    normalized_heading = heading.strip()
    if normalized_heading:
        lines.append(f"# {normalized_heading}")
        lines.append("")

    for label, value in properties:
        property_line = f"- **{label}:**"
        if value.strip():
            property_line = f"{property_line} {value.strip()}"
        lines.append(property_line)

    normalized_body = body.strip()
    if normalized_body:
        if lines:
            lines.append("")
        lines.append(normalized_body)

    return "\n".join(lines).rstrip() + "\n"


def _compose_npc_section_body(state_prefix: str) -> str:
    sections: list[str] = []
    for heading, state_key, _height in NPC_TEMPLATE_SECTION_FIELDS:
        section_content = str(
            st.session_state.get(f"{state_prefix}::section::{state_key}", "")
        ).strip()
        if section_content:
            sections.append(f"## {heading}\n\n{section_content}")
        else:
            sections.append(f"## {heading}")

    extra_body = str(st.session_state.get(f"{state_prefix}::extra_body", "")).strip()
    if extra_body:
        sections.append(extra_body)

    return "\n\n".join(section for section in sections if section.strip()).strip()


def _compose_scene_section_body(state_prefix: str) -> str:
    sections: list[str] = []
    for _display_label, markdown_heading, state_key, _height in SCENE_TEMPLATE_SECTION_FIELDS:
        section_content = str(
            st.session_state.get(f"{state_prefix}::section::{state_key}", "")
        ).strip()
        if section_content:
            sections.append(f"## {markdown_heading}\n\n{section_content}")
        else:
            sections.append(f"## {markdown_heading}")

    extra_body = str(st.session_state.get(f"{state_prefix}::extra_body", "")).strip()
    if extra_body:
        sections.append(extra_body)

    return "\n\n".join(section for section in sections if section.strip()).strip()


def _normalize_warning_lines(content: str) -> str:
    warning_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        warning_lines.append(stripped)
    return "\n".join(warning_lines)


def _compose_session_section_body(state_prefix: str) -> str:
    sections: list[str] = []
    current_goal = str(st.session_state.get(f"{state_prefix}::current_goal", "")).strip()
    if current_goal:
        sections.append(f"## Aktuelles Ziel\n\n{current_goal}")
    else:
        sections.append("## Aktuelles Ziel")

    warning_lines = [
        line.strip()
        for line in str(st.session_state.get(f"{state_prefix}::alerts", "")).splitlines()
        if line.strip()
    ]
    if warning_lines:
        sections.append(
            "## Warnungen\n\n" + "\n".join(f"- {line}" for line in warning_lines)
        )
    else:
        sections.append("## Warnungen")

    extra_body = str(st.session_state.get(f"{state_prefix}::extra_body", "")).strip()
    if extra_body:
        sections.append(extra_body)

    return "\n\n".join(section for section in sections if section.strip()).strip()


def _initialize_scene_editor_state(
    *,
    state_prefix: str,
    selection_key: str,
    content: str,
) -> None:
    loaded_state_key = f"{state_prefix}::loaded"
    if st.session_state.get(loaded_state_key) == selection_key:
        return

    frontmatter, body = _parse_frontmatter_dict(content)
    image_files = frontmatter.get("image_files") or []
    if not isinstance(image_files, (list, tuple)):
        image_files = [image_files]

    st.session_state[f"{state_prefix}::id"] = str(frontmatter.get("id", ""))
    st.session_state[f"{state_prefix}::title"] = str(
        frontmatter.get("title", selection_key)
    )
    st.session_state[f"{state_prefix}::status"] = str(
        frontmatter.get("status", "vorbereitet")
    )
    st.session_state[f"{state_prefix}::location"] = str(
        frontmatter.get("location", "")
    )
    st.session_state[f"{state_prefix}::source_file"] = str(
        frontmatter.get("source_file", "")
    )
    st.session_state[f"{state_prefix}::source_heading"] = str(
        frontmatter.get("source_heading", "")
    )
    st.session_state[f"{state_prefix}::image_files"] = "\n".join(
        str(value).strip() for value in image_files if str(value).strip()
    )
    body_without_heading = re.sub(
        r"^#\s+.+$",
        "",
        body,
        count=1,
        flags=re.MULTILINE,
    ).strip()
    sections, extra_body = _parse_scene_template_sections(body_without_heading)
    for _display_label, _markdown_heading, state_key, _height in SCENE_TEMPLATE_SECTION_FIELDS:
        st.session_state[f"{state_prefix}::section::{state_key}"] = sections[state_key]
    st.session_state[f"{state_prefix}::extra_body"] = extra_body
    st.session_state[f"{state_prefix}::extra_frontmatter"] = {
        key: value
        for key, value in frontmatter.items()
        if key not in SCENE_FRONTMATTER_FIELDS
    }
    st.session_state[loaded_state_key] = selection_key


def _session_scene_options(
    session_dir: Path,
    stored_scene_ids: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    scene_names = list_session_records(session_dir).get("Szenen", ())
    scene_labels_by_id: dict[str, str] = {}
    for scene_name in scene_names:
        scene_content = read_record_content(session_dir, "scene", scene_name)
        frontmatter, _body = _parse_frontmatter_dict(scene_content)
        scene_id = str(frontmatter.get("id", scene_name)).strip() or scene_name
        scene_title = str(frontmatter.get("title", scene_name)).strip() or scene_name
        scene_labels_by_id[scene_id] = scene_title

    ordered_options: list[tuple[str, str]] = []
    seen: set[str] = set()
    for scene_id in stored_scene_ids:
        normalized_scene_id = str(scene_id).strip()
        if not normalized_scene_id or normalized_scene_id in seen:
            continue
        ordered_options.append(
            (
                normalized_scene_id,
                scene_labels_by_id.get(normalized_scene_id, normalized_scene_id),
            )
        )
        seen.add(normalized_scene_id)

    for scene_id, scene_title in scene_labels_by_id.items():
        if scene_id in seen:
            continue
        ordered_options.append((scene_id, scene_title))

    return tuple(ordered_options)


def _initialize_session_editor_state(
    *,
    state_prefix: str,
    selection_key: str,
    content: str,
) -> None:
    loaded_state_key = f"{state_prefix}::loaded"
    if st.session_state.get(loaded_state_key) == selection_key:
        return

    frontmatter, body = _parse_frontmatter_dict(content)
    scene_ids = frontmatter.get("scene_ids") or []
    if not isinstance(scene_ids, (list, tuple)):
        scene_ids = [scene_ids]

    normalized_scene_ids = tuple(
        str(value).strip() for value in scene_ids if str(value).strip()
    )
    current_scene = str(frontmatter.get("current_scene", "")).strip()
    if current_scene and current_scene not in normalized_scene_ids:
        normalized_scene_ids = (current_scene, *normalized_scene_ids)

    sections, extra_body = _parse_session_template_sections(body)
    st.session_state[f"{state_prefix}::session_title"] = str(
        frontmatter.get("session_title", selection_key)
    )
    st.session_state[f"{state_prefix}::in_game_date"] = str(
        frontmatter.get("in_game_date", "")
    )
    st.session_state[f"{state_prefix}::region"] = str(frontmatter.get("region", ""))
    st.session_state[f"{state_prefix}::scene_ids"] = normalized_scene_ids
    st.session_state[f"{state_prefix}::current_scene"] = current_scene or (
        normalized_scene_ids[0] if normalized_scene_ids else ""
    )
    st.session_state[f"{state_prefix}::current_goal"] = sections["current_goal"]
    st.session_state[f"{state_prefix}::alerts"] = _normalize_warning_lines(
        sections["alerts"]
    )
    st.session_state[f"{state_prefix}::extra_body"] = extra_body
    st.session_state[f"{state_prefix}::extra_frontmatter"] = {
        key: value
        for key, value in frontmatter.items()
        if key not in SESSION_FRONTMATTER_FIELDS
    }
    st.session_state[loaded_state_key] = selection_key


def _build_scene_content_from_state(state_prefix: str) -> str:
    scene_id = str(st.session_state.get(f"{state_prefix}::id", "")).strip()
    title = str(st.session_state.get(f"{state_prefix}::title", "")).strip()
    status = str(st.session_state.get(f"{state_prefix}::status", "")).strip()
    location = str(st.session_state.get(f"{state_prefix}::location", "")).strip()
    source_file = str(st.session_state.get(f"{state_prefix}::source_file", "")).strip()
    source_heading = str(
        st.session_state.get(f"{state_prefix}::source_heading", "")
    ).strip()
    image_lines = str(st.session_state.get(f"{state_prefix}::image_files", "")).splitlines()
    image_files = [line.strip() for line in image_lines if line.strip()]
    body = _sync_first_heading(
        _compose_scene_section_body(state_prefix),
        title,
    )
    extra_frontmatter = dict(
        st.session_state.get(f"{state_prefix}::extra_frontmatter", {})
    )

    frontmatter = {
        "id": scene_id,
        "title": title,
        "status": status,
        "location": location,
    }
    if source_file:
        frontmatter["source_file"] = source_file
    if source_heading:
        frontmatter["source_heading"] = source_heading
    if image_files:
        frontmatter["image_files"] = image_files
    for key, value in extra_frontmatter.items():
        if key not in frontmatter:
            frontmatter[key] = value

    return _compose_frontmatter_content(frontmatter, body)


def _build_session_content_from_state(state_prefix: str) -> str:
    session_title = str(st.session_state.get(f"{state_prefix}::session_title", "")).strip()
    in_game_date = str(st.session_state.get(f"{state_prefix}::in_game_date", "")).strip()
    region = str(st.session_state.get(f"{state_prefix}::region", "")).strip()
    current_scene = str(st.session_state.get(f"{state_prefix}::current_scene", "")).strip()
    scene_ids = [
        str(value).strip()
        for value in tuple(st.session_state.get(f"{state_prefix}::scene_ids", ()))
        if str(value).strip()
    ]
    if current_scene and current_scene not in scene_ids:
        scene_ids.insert(0, current_scene)
    if not current_scene and scene_ids:
        current_scene = scene_ids[0]

    body = _compose_session_section_body(state_prefix)
    extra_frontmatter = dict(
        st.session_state.get(f"{state_prefix}::extra_frontmatter", {})
    )

    frontmatter = {
        "session_title": session_title,
        "in_game_date": in_game_date,
        "region": region,
        "current_scene": current_scene,
        "scene_ids": scene_ids,
    }
    for key, value in extra_frontmatter.items():
        if key not in frontmatter:
            frontmatter[key] = value

    return _compose_frontmatter_content(frontmatter, body)


def _initialize_npc_editor_state(
    *,
    state_prefix: str,
    selection_key: str,
    content: str,
) -> None:
    loaded_state_key = f"{state_prefix}::loaded"
    if st.session_state.get(loaded_state_key) == selection_key:
        return

    heading, properties, body = _parse_markdown_property_block(content)
    sections, extra_body = _parse_npc_template_sections(body)
    property_entries: list[dict[str, str]] = []
    for index, (label, value) in enumerate(properties):
        token = _build_state_token(label, index)
        property_entries.append({"label": label, "token": token})
        st.session_state[f"{state_prefix}::property::{token}"] = value

    st.session_state[f"{state_prefix}::heading"] = heading
    st.session_state[f"{state_prefix}::name"] = selection_key
    st.session_state[f"{state_prefix}::property_entries"] = property_entries
    for _heading, state_key, _height in NPC_TEMPLATE_SECTION_FIELDS:
        st.session_state[f"{state_prefix}::section::{state_key}"] = sections[state_key]
    st.session_state[f"{state_prefix}::extra_body"] = extra_body
    st.session_state[loaded_state_key] = selection_key


def _build_npc_content_from_state(state_prefix: str) -> str:
    property_entries = tuple(
        st.session_state.get(f"{state_prefix}::property_entries", ())
    )
    properties = tuple(
        (
            str(entry["label"]),
            str(
                st.session_state.get(
                    f"{state_prefix}::property::{entry['token']}",
                    "",
                )
            ),
        )
        for entry in property_entries
    )
    return _compose_markdown_property_content(
        heading=str(st.session_state.get(f"{state_prefix}::heading", "")),
        properties=properties,
        body=_compose_npc_section_body(state_prefix),
    )


def _render_npc_property_field(*, label: str, key: str) -> None:
    if label in NPC_EXPANDED_TEXT_FIELDS:
        st.text_area(label, key=key, height=68)
        return
    st.text_input(label, key=key)


def _render_npc_template_section_inputs(
    *,
    state_prefix: str,
    include_extra_body: bool,
) -> None:
    section_columns = st.columns(2, gap="large")
    split_index = (len(NPC_TEMPLATE_SECTION_FIELDS) + 1) // 2
    for index, (heading, state_key, height) in enumerate(NPC_TEMPLATE_SECTION_FIELDS):
        target_column = section_columns[0 if index < split_index else 1]
        with target_column:
            st.text_area(
                heading,
                key=f"{state_prefix}::section::{state_key}",
                height=height,
            )

    extra_body = str(st.session_state.get(f"{state_prefix}::extra_body", "")).strip()
    if include_extra_body or extra_body:
        with st.expander(
            "Zusaetzlicher Markdown-Inhalt",
            expanded=bool(extra_body),
        ):
            st.text_area(
                "Zusaetzlicher Markdown-Inhalt",
                key=f"{state_prefix}::extra_body",
                height=180,
            )


def _render_scene_template_section_inputs(
    *,
    state_prefix: str,
    include_extra_body: bool,
) -> None:
    section_columns = st.columns(2, gap="large")
    for index, (display_label, _markdown_heading, state_key, height) in enumerate(
        SCENE_TEMPLATE_SECTION_FIELDS
    ):
        target_column = section_columns[index % 2]
        with target_column:
            st.text_area(
                display_label,
                key=f"{state_prefix}::section::{state_key}",
                height=height,
            )

    extra_body = str(st.session_state.get(f"{state_prefix}::extra_body", "")).strip()
    if include_extra_body or extra_body:
        with st.expander(
            "Weiterer Markdown-Inhalt",
            expanded=bool(extra_body),
        ):
            st.text_area(
                "Weiterer Markdown-Inhalt",
                key=f"{state_prefix}::extra_body",
                height=220,
            )


def _render_session_template_section_inputs(
    *,
    state_prefix: str,
    include_extra_body: bool,
) -> None:
    st.text_area(
        "Aktuelles Ziel",
        key=f"{state_prefix}::current_goal",
        height=150,
    )
    st.text_area(
        "Warnungen (eine pro Zeile)",
        key=f"{state_prefix}::alerts",
        height=150,
    )

    extra_body = str(st.session_state.get(f"{state_prefix}::extra_body", "")).strip()
    if include_extra_body or extra_body:
        with st.expander(
            "Weiterer Markdown-Inhalt",
            expanded=bool(extra_body),
        ):
            st.text_area(
                "Weiterer Markdown-Inhalt",
                key=f"{state_prefix}::extra_body",
                height=180,
            )


def _render_npc_record_editor(
    *,
    session_dir: Path | None,
    label: str,
    names: tuple[str, ...],
) -> None:
    if session_dir is None:
        return
    if not names:
        st.caption(f"Noch keine {label.lower()} vorhanden.")
        return

    select_key = "sl_creator_edit_select::npc"
    default_name = st.session_state.get(select_key, names[0])
    if default_name not in names:
        default_name = names[0]

    selected_name = st.selectbox(
        f"Bestehende {label} bearbeiten",
        names,
        key=select_key,
    )
    file_content = read_record_content(session_dir, "npc", selected_name)
    state_prefix = "sl_creator_edit_form::npc"
    _initialize_npc_editor_state(
        state_prefix=state_prefix,
        selection_key=selected_name,
        content=file_content,
    )

    left_col, right_col = st.columns((1.15, 1), gap="large")
    with left_col:
        st.text_input(
            "Dateiname",
            value=str(st.session_state.get(f"{state_prefix}::name", selected_name)),
            disabled=True,
        )
        property_entries = tuple(
            st.session_state.get(f"{state_prefix}::property_entries", ())
        )
        property_columns = st.columns(2, gap="large")
        split_index = (len(property_entries) + 1) // 2
        for index, entry in enumerate(property_entries):
            target_column = property_columns[0 if index < split_index else 1]
            with target_column:
                _render_npc_property_field(
                    label=str(entry["label"]),
                    key=f"{state_prefix}::property::{entry['token']}",
                )
        st.markdown("**Template-Abschnitte**")
        _render_npc_template_section_inputs(
            state_prefix=state_prefix,
            include_extra_body=True,
        )

    with right_col:
        _render_preview_panel(_build_npc_content_from_state(state_prefix))

    submitted = st.button(
        "Aenderungen speichern",
        key="sl_creator_edit_save::npc",
        use_container_width=True,
    )

    if not submitted:
        return

    file_path = update_record_content(
        session_dir,
        "npc",
        selected_name,
        _build_npc_content_from_state(state_prefix),
    )
    st.session_state[FLASH_MESSAGE_KEY] = (
        f"{label} {file_path.stem} wurde aktualisiert."
    )
    st.rerun()


def _render_scene_record_editor(
    *,
    session_dir: Path | None,
    label: str,
    names: tuple[str, ...],
) -> None:
    if session_dir is None:
        return
    if not names:
        st.caption(f"Noch keine {label.lower()} vorhanden.")
        return

    select_key = "sl_creator_edit_select::scene"
    default_name = st.session_state.get(select_key, names[0])
    if default_name not in names:
        default_name = names[0]

    selected_name = st.selectbox(
        f"Bestehende {label} bearbeiten",
        names,
        key=select_key,
    )
    file_content = read_record_content(session_dir, "scene", selected_name)
    state_prefix = "sl_creator_edit_form::scene"
    _initialize_scene_editor_state(
        state_prefix=state_prefix,
        selection_key=selected_name,
        content=file_content,
    )

    left_col, right_col = st.columns((1.15, 1), gap="large")
    with left_col:
        st.text_input(
            "Interne ID",
            key=f"{state_prefix}::id",
            disabled=True,
        )
        meta_left_col, meta_right_col = st.columns(2)
        with meta_left_col:
            st.text_input(
                "Titel",
                key=f"{state_prefix}::title",
            )
            st.text_input(
                "Ort",
                key=f"{state_prefix}::location",
            )
            st.text_input(
                "Quell-Datei",
                key=f"{state_prefix}::source_file",
            )
        with meta_right_col:
            st.selectbox(
                "Status",
                _scene_status_options(
                    str(st.session_state.get(f"{state_prefix}::status", ""))
                ),
                key=f"{state_prefix}::status",
            )
            st.text_input(
                "Quell-Heading",
                key=f"{state_prefix}::source_heading",
            )
            st.text_area(
                "Bilddateien (eine pro Zeile)",
                key=f"{state_prefix}::image_files",
                height=90,
            )
        st.markdown("**Template-Abschnitte**")
        _render_scene_template_section_inputs(
            state_prefix=state_prefix,
            include_extra_body=True,
        )

    with right_col:
        _render_preview_panel(_build_scene_content_from_state(state_prefix))

    submitted = st.button(
        "Aenderungen speichern",
        key="sl_creator_edit_save::scene",
        use_container_width=True,
    )

    if not submitted:
        return

    if not str(st.session_state.get(f"{state_prefix}::title", "")).strip():
        st.error("Der Titel ist ein Pflichtfeld.")
        return

    file_path = update_record_content(
        session_dir,
        "scene",
        selected_name,
        _build_scene_content_from_state(state_prefix),
    )
    st.session_state[FLASH_MESSAGE_KEY] = (
        f"{label} {file_path.stem} wurde aktualisiert."
    )
    st.rerun()


def _record_editor(
    *,
    session_dir: Path | None,
    record_type: str,
    label: str,
    names: tuple[str, ...],
) -> None:
    if record_type == "scene":
        _render_scene_record_editor(
            session_dir=session_dir,
            label=label,
            names=names,
        )
        return

    if record_type == "npc":
        _render_npc_record_editor(
            session_dir=session_dir,
            label=label,
            names=names,
        )
        return

    if session_dir is None:
        return
    if not names:
        st.caption(f"Noch keine {label.lower()} vorhanden.")
        return

    select_key = f"sl_creator_edit_select::{record_type}"
    default_name = st.session_state.get(select_key, names[0])
    if default_name not in names:
        default_name = names[0]

    selected_name = st.selectbox(
        f"Bestehende {label} bearbeiten",
        names,
        key=select_key,
    )
    file_content = read_record_content(session_dir, record_type, selected_name)

    edited_content = _render_editor_with_preview(
        state_prefix=f"sl_creator_edit_form::{record_type}",
        selection_key=selected_name,
        content=file_content,
        height=320,
    )
    submitted = st.button(
        "Aenderungen speichern",
        key=f"sl_creator_edit_save::{record_type}",
        use_container_width=True,
    )

    if not submitted:
        return

    file_path = update_record_content(
        session_dir, record_type, selected_name, edited_content
    )
    st.session_state[FLASH_MESSAGE_KEY] = (
        f"{label} {file_path.stem} wurde aktualisiert."
    )
    st.rerun()


def _render_session_editor(session_dir: Path | None) -> None:
    if session_dir is None:
        st.caption("Waehle zuerst eine Session aus, um sie zu bearbeiten.")
        return

    file_content = read_session_content(session_dir)
    state_prefix = "sl_creator_edit_session"
    _initialize_session_editor_state(
        state_prefix=state_prefix,
        selection_key=session_dir.name,
        content=file_content,
    )
    scene_options = _session_scene_options(
        session_dir,
        tuple(st.session_state.get(f"{state_prefix}::scene_ids", ())),
    )
    scene_labels = {
        scene_id: scene_title for scene_id, scene_title in scene_options
    }

    left_col, right_col = st.columns((1.15, 1), gap="large")
    with left_col:
        meta_left_col, meta_right_col = st.columns(2)
        with meta_left_col:
            st.text_input(
                "Session-Name",
                key=f"{state_prefix}::session_title",
            )
            st.text_input(
                "Ingame-Datum",
                key=f"{state_prefix}::in_game_date",
            )
        with meta_right_col:
            st.text_input(
                "Region",
                key=f"{state_prefix}::region",
            )
            if scene_options:
                st.selectbox(
                    "Aktuelle Szene",
                    options=[scene_id for scene_id, _scene_title in scene_options],
                    format_func=lambda scene_id: scene_labels.get(scene_id, scene_id),
                    key=f"{state_prefix}::current_scene",
                )
            else:
                st.text_input(
                    "Aktuelle Szene",
                    key=f"{state_prefix}::current_scene",
                )
        st.caption(
            "Die Szenenreihenfolge bleibt bestehen und wird weiter ueber die Szenendateien verwaltet."
        )
        st.markdown("**Session-Inhalte**")
        _render_session_template_section_inputs(
            state_prefix=state_prefix,
            include_extra_body=True,
        )

    with right_col:
        _render_preview_panel(_build_session_content_from_state(state_prefix))

    submitted = st.button(
        "Session speichern",
        key="sl_creator_edit_session_save",
        use_container_width=True,
    )

    if not submitted:
        return

    if not str(st.session_state.get(f"{state_prefix}::session_title", "")).strip():
        st.error("Der Session-Name ist ein Pflichtfeld.")
        return

    file_path = update_session_content(
        session_dir,
        _build_session_content_from_state(state_prefix),
    )
    st.session_state[FLASH_MESSAGE_KEY] = (
        f"Session {file_path.parent.name} wurde aktualisiert."
    )
    st.rerun()


def _show_flash_message() -> None:
    message = st.session_state.pop(FLASH_MESSAGE_KEY, None)
    if message:
        st.success(message)


def render_new_session_form(
    selected_session_key_state: str,
    *,
    form_key_suffix: str,
    close_state_key: str | None = None,
) -> None:
    with st.form(f"sl_creator_new_session::{form_key_suffix}"):
        meta_col, detail_col = st.columns(2)
        with meta_col:
            title = st.text_input(
                "Session-Name",
                key=f"sl_creator_new_session_title::{form_key_suffix}",
            )
            in_game_date = st.text_input(
                "Ingame-Datum",
                key=f"sl_creator_new_session_date::{form_key_suffix}",
            )
        with detail_col:
            region = st.text_input(
                "Region",
                key=f"sl_creator_new_session_region::{form_key_suffix}",
            )
            st.caption(
                "Eine erste Szene wird automatisch angelegt. Weitere Angaben sind optional."
            )
        submitted = st.form_submit_button("Session anlegen", use_container_width=True)

    if not submitted:
        return

    if not title.strip():
        st.error("Session-Name ist ein Pflichtfeld.")
        return

    try:
        session_dir = create_session(
            title=title,
            in_game_date=in_game_date,
            region=region,
        )
    except FileExistsError as exc:
        st.error(str(exc))
        return

    st.session_state[selected_session_key_state] = session_dir.name
    if close_state_key is not None:
        st.session_state[close_state_key] = False
    st.session_state[FLASH_MESSAGE_KEY] = f"Session {session_dir.name} wurde angelegt."
    st.rerun()


def _session_overview(session_dir: Path | None) -> None:
    if session_dir is None:
        st.caption(
            "Lege eine neue Session an oder waehle oben eine bestehende Session aus."
        )
        return

    st.caption(f"Ausgewaehlte Session: {session_dir.name}")
    record_groups = list_session_records(session_dir)
    info_cols = st.columns(3)
    for column, (label, values) in zip(info_cols, record_groups.items()):
        with column:
            st.metric(label, len(values))

    expander_cols = st.columns(3, gap="large")
    for index, (label, values) in enumerate(record_groups.items()):
        with expander_cols[index % 3]:
            with st.expander(label, expanded=False):
                if not values:
                    st.caption(f"Noch keine {label.lower()} vorhanden.")
                else:
                    for value in values:
                        st.markdown(f"- {value}")


def _render_new_session_tab(selected_session_key_state: str) -> None:
    st.caption(
        "Neue Sessions legst du oben ueber den Button 'Neue Session' neben der Session-Auswahl an."
    )


def _render_workshop_section_control() -> str:
    section_options = tuple(WORKSHOP_SECTIONS)
    default_section = st.session_state.get(WORKSHOP_SECTION_KEY)
    if default_section not in WORKSHOP_SECTIONS:
        default_section = section_options[0]

    selected_section = st.segmented_control(
        "Werkstattbereich",
        section_options,
        default=default_section,
        format_func=lambda section: WORKSHOP_SECTIONS[section],
        key=WORKSHOP_SECTION_KEY,
        selection_mode="single",
        label_visibility="collapsed",
    )
    if selected_section is None:
        return default_section
    return int(selected_section)


def _render_overview_section(
    session_dir: Path | None,
    selected_session_key_state: str,
) -> None:
    _session_overview(session_dir)
    st.divider()
    _render_new_session_tab(selected_session_key_state)
    with st.expander("Session bearbeiten", expanded=True):
        _render_session_editor(session_dir)


def _render_scene_section(
    session_dir: Path | None,
    record_groups: dict[str, tuple[str, ...]],
) -> None:
    scene_tabs = st.tabs(["Neu", "Bearbeiten"])
    with scene_tabs[0]:
        _render_scene_tab(session_dir)
    with scene_tabs[1]:
        _record_editor(
            session_dir=session_dir,
            record_type="scene",
            label="Szenen",
            names=record_groups.get("Szenen", ()),
        )


def _render_npc_section(
    session_dir: Path | None,
    record_groups: dict[str, tuple[str, ...]],
) -> None:
    npc_tabs = st.tabs(["Neu", "Bearbeiten"])
    with npc_tabs[0]:
        _render_npc_tab(session_dir)
    with npc_tabs[1]:
        _record_editor(
            session_dir=session_dir,
            record_type="npc",
            label="NSCs",
            names=record_groups.get("NSCs", ()),
        )


def _render_monster_section(session_dir: Path | None) -> None:
    monster_tabs = st.tabs(["In Szene verlinken", "Bestiarium"])
    with monster_tabs[0]:
        _render_monster_link_tab(session_dir)
    with monster_tabs[1]:
        render_monster_creator_view()


def _render_combat_summary(session_dir: Path, scene_id: str) -> None:
    encounter_record = read_scene_encounter_record(session_dir, scene_id)
    if encounter_record is None:
        st.caption("Noch kein Combat fuer diese Szene angelegt.")
        return

    preparation = encounter_record.get("preparation")
    if not isinstance(preparation, dict):
        preparation = {}
    runtime = encounter_record.get("runtime")
    if not isinstance(runtime, dict):
        runtime = {}
    combatants = runtime.get("combatants")
    if not isinstance(combatants, list):
        combatants = []

    with st.container(border=True):
        status_col, round_col, amount_col = st.columns(3, gap="small")
        status_col.markdown("**Status**")
        status_col.caption(str(encounter_record.get("status", "draft")))
        round_col.markdown("**Runde**")
        round_col.caption(str(runtime.get("round_number", 1)))
        amount_col.markdown("**Combatants**")
        amount_col.caption(str(len(combatants)))

        source_keys = preparation.get("monster_source_keys")
        if isinstance(source_keys, list) and source_keys:
            st.markdown("**Bestiarium-Quellen**")
            for source_key in source_keys:
                st.write(f"- {source_key}")

        if not combatants:
            st.caption("Noch keine Combatants im Combat hinterlegt.")
            return

        st.markdown("**Aktuelle Combatants**")
        for combatant in combatants:
            if not isinstance(combatant, dict):
                continue
            name = str(combatant.get("name", "Unbenannter Combatant"))
            hp = combatant.get("current_hp", "-")
            max_hp = combatant.get("max_hp", "-")
            initiative = combatant.get("initiative", "-")
            source_key = str(combatant.get("source_key", "")).strip()
            st.markdown(f"**{name}**")
            details = [f"HP: {hp}/{max_hp}", f"Ini: {initiative}"]
            if source_key:
                details.append(f"Bestiarium: {source_key}")
            st.caption(" | ".join(details))


def _render_combat_section(
    session_dir: Path | None,
    record_groups: dict[str, tuple[str, ...]],
) -> None:
    if session_dir is None:
        st.caption("Waehle zuerst eine Session aus, um einen Combat zu bearbeiten.")
        return

    scene_names = record_groups.get("Szenen", ())
    if not scene_names:
        st.caption("Lege zuerst eine Szene an, bevor du einen Combat vorbereitest.")
        return

    bestiary_monsters = list_bestiary_monsters()
    side_options = ("enemy", "ally", "npc", "player")
    selected_scene_name = st.selectbox(
        "Szene",
        scene_names,
        key="sl_creator_combat_scene",
    )
    scene_id = get_scene_id(session_dir, selected_scene_name)
    encounter_record = read_scene_encounter_record(session_dir, scene_id)
    runtime = encounter_record.get("runtime", {}) if isinstance(encounter_record, dict) else {}
    if not isinstance(runtime, dict):
        runtime = {}
    combatants = runtime.get("combatants", [])
    if not isinstance(combatants, list):
        combatants = []

    left_col, right_col = st.columns((2, 1), gap="large")
    with left_col:
        _render_combat_summary(session_dir, scene_id)
    with right_col:
        if st.button(
            "Combat leeren",
            key=f"sl_creator_combat_clear::{scene_id}",
            use_container_width=True,
            type="secondary",
        ):
            update_scene_encounter_record(session_dir, scene_id, None)
            st.session_state[FLASH_MESSAGE_KEY] = (
                f"Combat fuer Szene {selected_scene_name} wurde geleert."
            )
            st.rerun()

    if combatants:
        st.divider()
        st.markdown("**Combat-Eintrag bearbeiten**")
        combatant_options = {
            f"{str(combatant.get('name', 'Unbenannter Combatant'))} ({str(combatant.get('id', ''))})": combatant
            for combatant in combatants
            if isinstance(combatant, dict)
        }
        selected_combatant_label = st.selectbox(
            "Combat-Eintrag",
            tuple(combatant_options.keys()),
            key="sl_creator_combat_edit_select",
        )
        selected_combatant = combatant_options[selected_combatant_label]
        selected_side = str(selected_combatant.get("side", "enemy")).strip() or "enemy"
        side_index = side_options.index(selected_side) if selected_side in side_options else 0

        edit_name_col, edit_side_col = st.columns(2, gap="small")
        with edit_name_col:
            edit_name = st.text_input(
                "Name im Combat",
                value=str(selected_combatant.get("name", "")),
                key="sl_creator_combat_edit_name",
            )
        with edit_side_col:
            edit_side = st.selectbox(
                "Seite",
                side_options,
                index=side_index,
                key="sl_creator_combat_edit_side",
            )

        edit_is_player = edit_side == "player"
        if edit_is_player:
            st.caption("Spieler tracken LP und RK selbst. Initiative wird im Kampftracker eingetragen.")

        meta_left_col, meta_right_col = st.columns(2, gap="large")
        with meta_left_col:
            if str(selected_combatant.get("source_key", "")).strip():
                st.caption(
                    f"Bestiarium-Link: {str(selected_combatant.get('source_key', '')).strip()}"
                )
        with meta_right_col:
            if not edit_is_player:
                edit_max_hp = st.number_input(
                    "Max HP",
                    min_value=1,
                    value=max(int(selected_combatant.get("max_hp", 1) or 1), 1),
                    step=1,
                    key="sl_creator_combat_edit_max_hp",
                )
                edit_current_hp = st.number_input(
                    "Aktuelle HP",
                    min_value=0,
                    value=max(int(selected_combatant.get("current_hp", 0) or 0), 0),
                    step=1,
                    key="sl_creator_combat_edit_current_hp",
                )
                edit_initiative = st.number_input(
                    "Initiative",
                    min_value=0,
                    value=max(int(selected_combatant.get("initiative", 0) or 0), 0),
                    step=1,
                    key="sl_creator_combat_edit_initiative",
                )
                edit_armor_class = st.number_input(
                    "RK",
                    min_value=0,
                    value=max(int(selected_combatant.get("armor_class", 0) or 0), 0),
                    step=1,
                    key="sl_creator_combat_edit_armor_class",
                )
            else:
                edit_max_hp = None
                edit_current_hp = None
                edit_initiative = None
                edit_armor_class = None
                st.caption("Initiative wird im Kampftracker eingetragen.")

        if st.button(
            "Combat-Eintrag speichern",
            key=f"sl_creator_combat_edit_save::{scene_id}",
            use_container_width=True,
        ):
            update_encounter_combatant(
                session_dir,
                scene_id,
                str(selected_combatant.get("id", "")).strip(),
                name=edit_name,
                side=edit_side,
                max_hp=None if edit_max_hp is None else int(edit_max_hp),
                current_hp=None if edit_current_hp is None else int(edit_current_hp),
                initiative=None if edit_initiative is None else int(edit_initiative),
                armor_class=None if edit_armor_class is None else int(edit_armor_class),
            )
            st.session_state[FLASH_MESSAGE_KEY] = (
                f"Combat-Eintrag fuer {selected_scene_name} wurde aktualisiert."
            )
            st.rerun()

    st.divider()
    st.markdown("**Combat-Eintrag anlegen**")
    create_name_col, create_side_col = st.columns(2, gap="small")
    with create_name_col:
        display_name = st.text_input(
            "Name im Combat",
            key="sl_creator_combat_display_name",
        )
    with create_side_col:
        create_side = st.selectbox(
            "Seite",
            side_options,
            key="sl_creator_combat_side",
        )

    if create_side == "player":
        st.caption("Spieler tracken LP und RK selbst. Initiative wird im Kampftracker eingetragen.")
        if not st.button(
            "Spieler in Combat einbauen",
            key=f"sl_creator_combat_add_player::{scene_id}",
            use_container_width=True,
        ):
            return

        if not display_name.strip():
            st.error("Name im Combat ist fuer Spieler ein Pflichtfeld.")
            return

        file_path = add_player_combatant_to_encounter(
            session_dir,
            scene_id,
            display_name,
        )
        st.session_state[FLASH_MESSAGE_KEY] = (
            f"{display_name.strip()} wurde als Spieler fuer {selected_scene_name} eingebaut ({file_path.name})."
        )
        st.rerun()

    if not bestiary_monsters:
        st.caption("Im Bestiarium sind noch keine Monster vorhanden.")
        return

    monster_name = st.selectbox(
        "Bestiarium-Monster",
        bestiary_monsters,
        key="sl_creator_combat_monster",
    )
    resolved_armor_class = get_bestiary_armor_class(monster_name)
    st.caption("Ohne Namen wird der Bestiariumsname als Combat-Name verwendet.")

    stats_col, initiative_col, ac_col = st.columns(3)
    with stats_col:
        max_hp = st.number_input(
            "Lebenspunkte",
            min_value=1,
            value=10,
            step=1,
            key="sl_creator_combat_hp",
        )
    with initiative_col:
        initiative = st.number_input(
            "Initiative",
            min_value=0,
            value=10,
            step=1,
            key="sl_creator_combat_initiative",
        )
    with ac_col:
        armor_class = st.number_input(
            "RK",
            min_value=0,
            value=resolved_armor_class or 10,
            step=1,
            key="sl_creator_combat_ac",
            disabled=True,
        )
        if resolved_armor_class is None:
            st.caption("Keine RK im Bestiarium gefunden, Fallback 10.")
        else:
            st.caption("RK wurde aus dem Bestiarium gelesen.")

    if not st.button(
        "Monster in Combat einbauen",
        key=f"sl_creator_combat_add::{scene_id}",
        use_container_width=True,
    ):
        return

    file_path = add_bestiary_combatant_to_encounter(
        session_dir,
        scene_id,
        monster_name,
        max_hp=int(max_hp),
        initiative=int(initiative),
        display_name=display_name,
        side=create_side,
    )
    st.session_state[FLASH_MESSAGE_KEY] = (
        f"{monster_name} wurde in den Combat fuer {selected_scene_name} eingebaut ({file_path.name})."
    )
    st.rerun()


def _render_scene_tab(session_dir: Path | None) -> None:
    if session_dir is None:
        st.caption("Waehle zuerst eine Session aus, um neue Szenen anzulegen.")
        return

    with st.form("sl_creator_new_scene"):
        left_col, right_col = st.columns(2)
        with left_col:
            title = st.text_input("Szenenname")
            location = st.text_input("Ort")
            status = st.selectbox("Status", ("vorbereitet", "aktiv", "spaeter"))
        with right_col:
            atmosphere = st.text_area("Atmosphaere", height=90)
            goal = st.text_area("Ziel", height=90)
            pressure = st.text_area("Druck", height=90)
        summary = st.text_area("Szenenbild", height=100)
        submitted = st.form_submit_button("Szene anlegen", use_container_width=True)

    if not submitted:
        return

    if not title.strip():
        st.error("Der Szenenname ist ein Pflichtfeld.")
        return

    try:
        file_path = create_scene(
            session_dir=session_dir,
            title=title,
            location=location,
            status=status,
            summary=summary,
            atmosphere=atmosphere,
            goal=goal,
            pressure=pressure,
        )
    except FileExistsError as exc:
        st.error(str(exc))
        return

    st.session_state[FLASH_MESSAGE_KEY] = f"Szene {file_path.stem} wurde angelegt."
    st.rerun()


def _render_npc_tab(session_dir: Path | None) -> None:
    if session_dir is None:
        st.caption("Waehle zuerst eine Session aus, um NSCs anzulegen.")
        return

    with st.form("sl_creator_new_npc"):
        left_col, right_col = st.columns(2)
        with left_col:
            name = st.text_input("Name")
            title = st.text_input("Titel / Amt")
        with right_col:
            species = st.text_input("Spezies / Volk", value="Mensch")
            origin = st.text_input("Herkunft")

        section_state_prefix = "sl_creator_new_npc"
        st.markdown("**Template-Abschnitte**")
        _render_npc_template_section_inputs(
            state_prefix=section_state_prefix,
            include_extra_body=False,
        )
        submitted = st.form_submit_button("NSC anlegen", use_container_width=True)

    if not submitted:
        return

    if not name.strip():
        st.error("Der Name ist ein Pflichtfeld.")
        return

    try:
        file_path = create_npc(
            session_dir=session_dir,
            name=name,
            title=title,
            species=species,
            origin=origin,
            description=str(
                st.session_state.get(
                    f"{section_state_prefix}::section::description", ""
                )
            ),
            role_relationships=str(
                st.session_state.get(
                    f"{section_state_prefix}::section::role_relationships", ""
                )
            ),
            goals=str(
                st.session_state.get(f"{section_state_prefix}::section::goals", "")
            ),
            plot_hooks=str(
                st.session_state.get(
                    f"{section_state_prefix}::section::plot_hooks", ""
                )
            ),
            secret_information=str(
                st.session_state.get(
                    f"{section_state_prefix}::section::secret_information", ""
                )
            ),
            combat_values=str(
                st.session_state.get(
                    f"{section_state_prefix}::section::combat_values", ""
                )
            ),
        )
    except FileExistsError as exc:
        st.error(str(exc))
        return

    st.session_state[FLASH_MESSAGE_KEY] = f"NSC {file_path.stem} wurde angelegt."
    st.rerun()


def _render_monster_link_tab(session_dir: Path | None) -> None:
    if session_dir is None:
        st.caption("Waehle zuerst eine Session aus, um Monster zu verlinken.")
        return

    scene_names = list_session_records(session_dir).get("Szenen", ())
    bestiary_monsters = list_bestiary_monsters()
    if not scene_names:
        st.caption("Lege zuerst eine Szene an, bevor du Monster verlinkst.")
        return
    if not bestiary_monsters:
        st.caption("Im Bestiarium sind noch keine Monster vorhanden.")
        return

    with st.form("sl_creator_link_monster"):
        left_col, right_col = st.columns(2)
        with left_col:
            scene_name = st.selectbox("Szene", scene_names)
        with right_col:
            monster_name = st.selectbox("Bestiarium-Monster", bestiary_monsters)
        submitted = st.form_submit_button(
            "In Szene verlinken", use_container_width=True
        )

    if not submitted:
        return

    try:
        file_path = link_bestiary_monster_to_scene(
            session_dir=session_dir,
            scene_name=scene_name,
            monster_name=monster_name,
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    st.session_state[FLASH_MESSAGE_KEY] = (
        f"{monster_name} wurde in {file_path.stem} verlinkt."
    )
    st.rerun()


def render_creator_view(
    *,
    session_dir: Path | None,
    selected_session_key_state: str,
) -> None:
    _show_flash_message()
    st.subheader("Werkstatt")
    selected_section = _render_workshop_section_control()
    record_groups = list_session_records(session_dir) if session_dir is not None else {}

    if selected_section == WORKSHOP_SECTION_OVERVIEW:
        _render_overview_section(session_dir, selected_session_key_state)
    elif selected_section == WORKSHOP_SECTION_SCENES:
        _render_scene_section(session_dir, record_groups)
    elif selected_section == WORKSHOP_SECTION_NPCS:
        _render_npc_section(session_dir, record_groups)
    elif selected_section == WORKSHOP_SECTION_MONSTERS:
        _render_monster_section(session_dir)
    else:
        _render_combat_section(session_dir, record_groups)
