from pathlib import Path

import streamlit as st

from wiki_dasboard.config import DashboardViewConfig, cfg
from wiki_dasboard.components.show_file import show_image
from wiki_dasboard.components import utils


DEFAULT_DASHBOARD_TEXT = (
    "Navigiere mit der Sidebar durch das Wiki und erkunde die Ecken von Andaros. "
    "Mit zurück kommst du in den vorherigen Ordner. Viel Spaß und melde dich, "
    "wenn du mal wieder eine Runde in diesem Universum spielen willst."
)
CAMPAIGN_OVERVIEW_EXPANDED_KEY = "campaign_overview_expanded_folders"


def _is_collection_path(path: str) -> bool:
    collection_names = {name.casefold() for name in cfg.navigation.databases}
    return any(part.casefold() in collection_names for part in Path(path).parts)


def _toggle_campaign_overview_folder(path: str) -> None:
    expanded = set(st.session_state.get(CAMPAIGN_OVERVIEW_EXPANDED_KEY, []))
    if path in expanded:
        expanded.remove(path)
    else:
        expanded.add(path)
    st.session_state[CAMPAIGN_OVERVIEW_EXPANDED_KEY] = sorted(expanded)


def render_default_dashboard() -> None:
    st.text(DEFAULT_DASHBOARD_TEXT)
    cols = st.columns([1, 7])
    for emblem in cfg.layout.default_emblems:
        show_image(cols[0], emblem)
    show_image(cols[1], cfg.layout.default_background)


def render_vertical_spacing(spacing_rem: float) -> None:
    if spacing_rem <= 0:
        return
    st.markdown(
        f'<div style="height: {spacing_rem}rem;"></div>',
        unsafe_allow_html=True,
    )


def render_timeline_dashboard(view: DashboardViewConfig) -> None:
    if view.asset_path is None:
        render_default_dashboard()
        return

    timeline_path = utils.resolve_dashboard_asset_path(view)
    if timeline_path is None:
        st.info(
            f"Timeline nicht gefunden: {view.asset_path}. Fallback auf Standardansicht."
        )
        render_default_dashboard()
        return

    render_vertical_spacing(view.top_spacing_rem)
    target = st
    if view.layout_columns is not None:
        columns = st.columns(view.layout_columns)
        target = columns[1]

    target.image(str(timeline_path), use_container_width=view.use_container_width)
    if view.caption:
        target.caption(view.caption)


def render_dashboard(view: DashboardViewConfig | None) -> None:
    if view is None or view.mode == "default":
        render_default_dashboard()
        return

    if view.mode == "timeline":
        render_timeline_dashboard(view)
        return

    render_default_dashboard()


def render_campaign_overview(tree: dict) -> None:
    root_tree = tree.get(st.session_state["root_path"], {})
    if not root_tree:
        st.info("Für diese Kampagne sind keine Dokumente sichtbar.")
        return

    if CAMPAIGN_OVERVIEW_EXPANDED_KEY not in st.session_state:
        st.session_state[CAMPAIGN_OVERVIEW_EXPANDED_KEY] = [
            path
            for path, value in root_tree.items()
            if path != "__files__"
            and isinstance(value, dict)
            and not _is_collection_path(path)
        ]

    def item_target(depth: int):
        if depth <= 0:
            return st
        columns = st.columns([min(depth, 4), 12])
        return columns[1]

    def render_tree(subtree: dict, depth: int) -> None:
        folders = sorted(
            key
            for key, value in subtree.items()
            if key != "__files__"
            and isinstance(value, dict)
            and not _is_collection_path(key)
        )
        for folder in folders:
            expanded = folder in st.session_state[CAMPAIGN_OVERVIEW_EXPANDED_KEY]
            item_target(depth).button(
                utils.format_path(folder),
                key=f"campaign-overview-folder::{folder}",
                icon=(
                    ":material/keyboard_arrow_down:"
                    if expanded
                    else ":material/keyboard_arrow_right:"
                ),
                help="Ordner schließen" if expanded else "Ordner öffnen",
                on_click=_toggle_campaign_overview_folder,
                args=(folder,),
                use_container_width=True,
                type="tertiary",
            )
            if expanded:
                render_tree(subtree[folder], depth + 1)

        files = sorted(
            path
            for path in subtree.get("__files__", [])
            if not _is_collection_path(path)
        )
        for path in files:
            item_target(depth).button(
                f"📄 {utils.format_path(path)}",
                key=f"campaign-overview::{path}",
                on_click=utils.set_path,
                args=(path,),
                use_container_width=True,
                type="tertiary",
            )

    render_tree(root_tree, 0)
