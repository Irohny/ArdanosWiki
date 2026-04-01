from pathlib import Path
import re

import streamlit as st

from components.monster_creator import render_monster_creator_view
from sl_dashboard.components.markdown import render_wiki_markdown
from sl_dashboard.editor import (
    create_npc,
    create_scene,
    create_session,
    link_bestiary_monster_to_scene,
    list_bestiary_monsters,
    read_record_content,
    read_session_content,
    list_session_records,
    update_record_content,
    update_session_content,
)


FLASH_MESSAGE_KEY = "sl_creator_flash_message"


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


def _record_editor(
    *,
    session_dir: Path | None,
    record_type: str,
    label: str,
    names: tuple[str, ...],
) -> None:
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
    edited_content = _render_editor_with_preview(
        state_prefix="sl_creator_edit_session",
        selection_key=session_dir.name,
        content=file_content,
        height=320,
    )
    submitted = st.button(
        "Session speichern",
        key="sl_creator_edit_session_save",
        use_container_width=True,
    )

    if not submitted:
        return

    file_path = update_session_content(session_dir, edited_content)
    st.session_state[FLASH_MESSAGE_KEY] = (
        f"Session {file_path.parent.name} wurde aktualisiert."
    )
    st.rerun()


def _show_flash_message() -> None:
    message = st.session_state.pop(FLASH_MESSAGE_KEY, None)
    if message:
        st.success(message)


def _session_overview(session_dir: Path | None) -> None:
    st.subheader("Werkstatt")
    if session_dir is None:
        st.caption(
            "Lege eine neue Session an oder waehle eine bestehende Session in der Sidebar aus."
        )
        return

    st.caption(f"Ausgewaehlte Session: {session_dir.name}")
    record_groups = list_session_records(session_dir)
    info_cols = st.columns(3)
    for column, (label, values) in zip(info_cols, record_groups.items()):
        with column:
            st.metric(label, len(values))

    for label, values in record_groups.items():
        with st.expander(label, expanded=False):
            if not values:
                st.caption(f"Noch keine {label.lower()} vorhanden.")
            else:
                for value in values:
                    st.markdown(f"- {value}")


def _render_new_session_tab(selected_session_key_state: str) -> None:
    with st.form("sl_creator_new_session"):
        meta_col, scene_col = st.columns(2)
        with meta_col:
            title = st.text_input("Session-Name")
            in_game_date = st.text_input("Ingame-Datum")
            region = st.text_input("Region")
            source_story = st.text_input(
                "Quellgeschichte", placeholder="World/.../Datei.md"
            )
        with scene_col:
            pacing = st.text_area("Pacing", height=100)
            first_scene_title = st.text_input("Titel der ersten Szene")
            first_scene_location = st.text_input("Ort der ersten Szene")
        st.markdown("**Startszene**")
        submitted = st.form_submit_button("Session anlegen", use_container_width=True)

    if not submitted:
        return

    if not title.strip() or not first_scene_title.strip():
        st.error("Session-Name und erste Szene sind Pflichtfelder.")
        return

    try:
        session_dir = create_session(
            title=title,
            in_game_date=in_game_date,
            region=region,
            pacing=pacing,
            first_scene_title=first_scene_title,
            first_scene_location=first_scene_location,
            source_story=source_story,
        )
    except FileExistsError as exc:
        st.error(str(exc))
        return

    st.session_state[selected_session_key_state] = session_dir.name
    st.session_state[FLASH_MESSAGE_KEY] = f"Session {session_dir.name} wurde angelegt."
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
        description = st.text_area("Beschreibung und Auftreten", height=110)
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
            description=description,
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
    _session_overview(session_dir)
    record_groups = list_session_records(session_dir) if session_dir is not None else {}

    tabs = st.tabs(["Session", "Szene", "NSC", "Monster", "Bestiarium-Monster"])
    with tabs[0]:
        session_tabs = st.tabs(["Neu", "Bearbeiten"])
        with session_tabs[0]:
            _render_new_session_tab(selected_session_key_state)
        with session_tabs[1]:
            _render_session_editor(session_dir)
    with tabs[1]:
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
    with tabs[2]:
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
    with tabs[3]:
        _render_monster_link_tab(session_dir)
    with tabs[4]:
        render_monster_creator_view()
