import re
from pathlib import Path
from urllib.parse import urlencode, unquote

import streamlit as st

from sl_dashboard.components.quick_access import render_active_npcs, render_quick_links
from sl_dashboard.components.theme import apply_sl_parchment_theme
from config import cfg
from sl_dashboard.components.markdown import (
    ACTIVE_SCENE_QUERY_PARAM,
    LINKED_WIKI_PAGE_QUERY_PARAM,
    render_wiki_markdown,
    set_query_param,
)
from sl_dashboard.components.scene_focus import (
    render_next_scenes,
    render_scene_focus_card,
)
from sl_dashboard.models import DashboardData


ACTIVE_SCENE_STATE_KEY = "sl_dashboard_active_scene"
ACTIVE_DETAIL_STATE_KEY = "sl_dashboard_active_detail"
REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


@st.cache_data
def _collect_images() -> dict[str, str]:
    images: dict[str, str] = {}
    for file_path in (REPO_ROOT / "World").rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            images[file_path.name] = str(file_path.resolve())
    return images


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

    return "\n".join(lines[start_index:end_index])


def _extract_embedded_images(file_path: str, heading: str = "") -> tuple[str, ...]:
    source_path = REPO_ROOT / file_path
    if not source_path.exists():
        return ()

    content = _extract_section_content(source_path, heading)
    embedded_files = re.findall(r"!\[\[([^\]]+)\]\]", content)
    image_names: list[str] = []
    for embedded_file in embedded_files:
        image_name = embedded_file.split("|")[0].strip()
        if Path(image_name).suffix.lower() in IMAGE_EXTENSIONS:
            image_names.append(image_name)
    return tuple(image_names)


def _prepare_markdown_for_panel(content: str) -> str:
    content = re.sub(r"!\[\[([^\]]+)\]\]", "", content)
    content = re.sub(r"\[\[([^\]]+)\]\]", lambda match: match.group(1), content)
    return content.strip()


def _read_source_markdown(
    file_path: str,
    *,
    heading: str = "",
) -> str:
    source_path = Path(file_path)
    if not source_path.is_absolute():
        source_path = REPO_ROOT / file_path
    if not source_path.exists():
        return ""

    raw_content = _extract_section_content(source_path, heading)
    return _prepare_markdown_for_panel(raw_content)


def _normalize_reference_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _extract_scene_reference_tokens(scene) -> tuple[str, ...]:
    values = [
        scene.summary,
        scene.pressure,
        *scene.stakes,
        *scene.discoveries,
        *scene.likely_player_actions,
        *scene.hidden_truths,
    ]
    tokens: list[str] = []
    for value in values:
        tokens.extend(match.strip() for match in WIKI_LINK_PATTERN.findall(str(value)))
    return tuple(tokens)


def _item_reference_keys(
    *, title: str, source_file: str = "", source_heading: str = ""
) -> tuple[str, ...]:
    keys: list[str] = []
    if title:
        keys.append(_normalize_reference_key(title))
    if source_file:
        keys.append(_normalize_reference_key(Path(source_file).stem))
    if source_heading:
        keys.append(_normalize_reference_key(source_heading.lstrip("# ")))

    deduped: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if not key or key in seen:
            continue
        deduped.append(key)
        seen.add(key)
    return tuple(deduped)


def _filter_references_for_active_scene(
    data: DashboardData, active_scene
) -> tuple[tuple, tuple, tuple]:
    active_keys = {
        _normalize_reference_key(token)
        for token in _extract_scene_reference_tokens(active_scene)
        if token.strip()
    }
    if not active_keys:
        return ((), (), ())

    place_links = tuple(
        link
        for link in data.quick_links
        if link.context.casefold() == "ort"
        and any(
            key in active_keys
            for key in _item_reference_keys(
                title=link.title,
                source_file=link.source_file,
                source_heading=link.source_heading,
            )
        )
    )
    monster_links = tuple(
        link
        for link in data.quick_links
        if link.context.casefold() == "monster"
        and any(
            key in active_keys
            for key in _item_reference_keys(
                title=link.title,
                source_file=link.source_file,
                source_heading=link.source_heading,
            )
        )
    )
    npcs = tuple(
        npc
        for npc in data.npcs
        if any(
            key in active_keys
            for key in _item_reference_keys(
                title=npc.name,
                source_file=npc.source_file,
                source_heading=npc.source_heading,
            )
        )
    )
    return (place_links, npcs, monster_links)


def _resolve_image_paths(image_names: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    images = _collect_images()
    resolved_images: list[tuple[str, str]] = []
    for image_name in image_names:
        image_path = images.get(image_name)
        if image_path is not None:
            resolved_images.append((image_name, image_path))
    return tuple(resolved_images)


def _render_scene_images(active_scene) -> None:
    with st.container(border=True):
        if not active_scene.source_file:
            st.caption("Fuer diese Szene ist keine Bildquelle hinterlegt.")
            return

        image_names = active_scene.image_files or _extract_embedded_images(
            active_scene.source_file,
            active_scene.source_heading,
        )
        if not image_names:
            st.caption(
                "In der Szenenquelle wurden keine eingebetteten Bilder gefunden."
            )
            return

        resolved_images = _resolve_image_paths(image_names)
        for image_name, image_path in resolved_images:
            st.image(image_path, use_container_width=True)

        resolved_names = {image_name for image_name, _ in resolved_images}
        for image_name in image_names:
            if image_name in resolved_names:
                continue
            st.caption(f"Bild nicht gefunden: {image_name}")


def _render_linked_wiki_page() -> None:
    selected_page = st.query_params.get(LINKED_WIKI_PAGE_QUERY_PARAM)
    if not selected_page:
        st.caption("Noch keine verlinkte Wiki-Seite geoeffnet.")
        return

    selected_page = unquote(str(selected_page))
    selected_page_name = Path(selected_page).stem or "Wiki-Seite"
    wiki_page_href = f"{cfg.WIKI_APP_BASE_URL}/?{urlencode({'page': selected_page})}"

    with st.container(border=True):
        header_col, open_col, close_col = st.columns(
            (4, 2, 1), vertical_alignment="center"
        )
        header_col.markdown(f"**{selected_page_name}**")
        open_col.link_button(
            "->",
            url=wiki_page_href,
            use_container_width=True,
            type="secondary",
        )
        close_col.button(
            "x",
            key="sl-linked-page-close",
            use_container_width=True,
            help="Verlinkte Wiki-Seite schließen",
            on_click=set_query_param,
            args=(LINKED_WIKI_PAGE_QUERY_PARAM, None),
        )
        content = _read_source_markdown(str(selected_page))
        if not content:
            st.caption("Die verlinkte Wiki-Seite konnte nicht geladen werden.")
            return
        render_wiki_markdown(content)


def _render_right_column_tabs(
    active_scene,
    npcs: tuple,
    monster_links: tuple,
    *,
    detail_type: str | None,
    selected_title: str | None,
) -> None:
    tabs = st.tabs(["Infos", "NSCs", "Monster"])

    with tabs[0]:
        _render_scene_images(active_scene)
        _render_linked_wiki_page()

    with tabs[1]:
        render_active_npcs(
            npcs,
            active_name=selected_title if detail_type == "NSC" else None,
        )

    with tabs[2]:
        render_quick_links(
            monster_links,
            active_title=selected_title if detail_type == "Monster" else None,
        )


def _resolve_active_scene(data: DashboardData):
    scenes = (data.current_scene, *data.next_scenes)
    scene_titles = {scene.title for scene in scenes}
    query_scene_title = st.query_params.get(ACTIVE_SCENE_QUERY_PARAM)
    if query_scene_title in scene_titles:
        st.session_state[ACTIVE_SCENE_STATE_KEY] = str(query_scene_title)
    elif ACTIVE_SCENE_STATE_KEY not in st.session_state:
        st.session_state[ACTIVE_SCENE_STATE_KEY] = data.current_scene.title

    selected_title = st.session_state[ACTIVE_SCENE_STATE_KEY]
    for scene in scenes:
        if scene.title == selected_title:
            set_query_param(ACTIVE_SCENE_QUERY_PARAM, scene.title)
            return scene, scenes

    st.session_state[ACTIVE_SCENE_STATE_KEY] = data.current_scene.title
    set_query_param(ACTIVE_SCENE_QUERY_PARAM, data.current_scene.title)
    return data.current_scene, scenes


def _order_scenes_for_sidebar(
    scenes: tuple,
    active_scene_title: str,
) -> tuple:
    if not scenes:
        return scenes

    active_index = next(
        (
            index
            for index, scene in enumerate(scenes)
            if scene.title == active_scene_title
        ),
        0,
    )
    return scenes[active_index:] + scenes[:active_index]


def _resolve_scene_neighbors(
    scenes: tuple,
    active_scene_title: str,
) -> tuple[str | None, str | None]:
    if not scenes:
        return (None, None)
    if len(scenes) == 1:
        return (None, None)

    active_index = next(
        (
            index
            for index, scene in enumerate(scenes)
            if scene.title == active_scene_title
        ),
        0,
    )
    previous_scene_title = scenes[(active_index - 1) % len(scenes)].title
    next_scene_title = scenes[(active_index + 1) % len(scenes)].title
    return (previous_scene_title, next_scene_title)


def _resolve_active_detail(data: DashboardData) -> tuple[str | None, str | None]:
    default_detail = next(
        (npc.name for npc in data.npcs),
        None,
    ) or next(
        (
            link.title
            for link in data.quick_links
            if link.context.casefold() == "monster"
        ),
        None,
    )
    if ACTIVE_DETAIL_STATE_KEY not in st.session_state:
        st.session_state[ACTIVE_DETAIL_STATE_KEY] = default_detail

    selected_title = st.session_state[ACTIVE_DETAIL_STATE_KEY]
    if selected_title is None:
        return (None, None)

    for link in data.quick_links:
        if link.title == selected_title and link.context.casefold() == "monster":
            return (link.context, link.title)

    for npc in data.npcs:
        if npc.name == selected_title:
            return ("NSC", npc.name)

    st.session_state[ACTIVE_DETAIL_STATE_KEY] = default_detail
    if default_detail is None:
        return (None, None)
    for npc in data.npcs:
        if npc.name == default_detail:
            return ("NSC", npc.name)
    return ("Monster", default_detail)


def render_sl_dashboard_shell(data: DashboardData) -> None:
    apply_sl_parchment_theme()
    active_scene, all_scenes = _resolve_active_scene(data)
    ordered_sidebar_scenes = _order_scenes_for_sidebar(all_scenes, active_scene.title)
    previous_scene_title, next_scene_title = _resolve_scene_neighbors(
        all_scenes,
        active_scene.title,
    )
    detail_type, selected_title = _resolve_active_detail(data)
    active_place_links, active_npcs, active_monster_links = (
        _filter_references_for_active_scene(
            data,
            active_scene,
        )
    )

    st.header(data.status.session_title)
    st.caption(
        f"Datum: {data.status.in_game_date}, Region: {data.status.region}, aktive Szene: {active_scene.title}"
    )

    left_col, center_col, right_col = st.columns((1, 4, 2), gap="large")

    with left_col:
        render_next_scenes(
            ordered_sidebar_scenes,
            active_scene.title,
            state_key=ACTIVE_SCENE_STATE_KEY,
        )

    with center_col:
        render_scene_focus_card(
            active_scene,
            state_key=ACTIVE_SCENE_STATE_KEY,
            previous_scene_title=previous_scene_title,
            next_scene_title=next_scene_title,
        )

    with right_col:
        _render_right_column_tabs(
            active_scene,
            active_npcs,
            active_monster_links,
            detail_type=detail_type,
            selected_title=selected_title,
        )
