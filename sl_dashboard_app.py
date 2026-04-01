from pathlib import Path

import streamlit as st

from components import utils
from components.header import header
from components.file_parser import build_markdown_database
from components.login import Roles, User
from components.sidebar import create_sidebar
from config import cfg
from sl_dashboard import render_sl_dashboard
from sl_dashboard.creator_view import render_creator_view
from sl_dashboard.components.markdown import LINKED_WIKI_PAGE_QUERY_PARAM
from sl_dashboard.components.theme import apply_sl_parchment_theme
from sl_dashboard.loader import get_session_dir_by_key, list_available_sessions


SESSION_SELECT_KEY = "sl_dashboard_selected_session"
CREATOR_MODE_KEY = "sl_dashboard_creator_mode"


def _resolve_page_title() -> str:
    selected_page = st.query_params.get("page")
    if not selected_page:
        return "SL-Dashboard"

    return Path(str(selected_page)).stem


def _initialize_wiki_context() -> None:
    if "root_path" in st.session_state:
        return

    st.session_state["user"] = User(name="SL", role=Roles.GameMaster, loged_in=True)
    st.session_state["tree"] = utils.find_markdown_files(
        cfg.MARKDOWN_DIR, st.session_state["user"]
    )
    st.session_state["images"] = utils.collect_images_by_name(cfg.IMAGE_DIR)
    st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
    st.session_state["current_path"] = st.session_state["root_path"]
    st.session_state["db_flag"] = False
    st.session_state["db"] = ""
    for db in cfg.DATABASE_LIST:
        if db not in st.session_state:
            st.session_state[db] = build_markdown_database(f"World/{db}")


def _render_session_sidebar() -> tuple[bool, str | None]:
    session_options = list_available_sessions()

    st.sidebar.header("SL-Sessions")
    creator_mode = st.sidebar.toggle("Erstellungsansicht", key=CREATOR_MODE_KEY)
    if not session_options:
        if creator_mode:
            st.sidebar.caption(
                "Noch keine Session-Daten vorhanden. Lege in der Werkstatt eine neue Session an."
            )
        else:
            st.sidebar.caption("Keine Session-Daten gefunden.")
        return (creator_mode, None)

    option_keys = [option.key for option in session_options]
    if SESSION_SELECT_KEY not in st.session_state:
        st.session_state[SESSION_SELECT_KEY] = option_keys[0]

    selected_key = st.sidebar.selectbox(
        "Aktive Session",
        option_keys,
        key=SESSION_SELECT_KEY,
        format_func=lambda key: next(
            option.title for option in session_options if option.key == key
        ),
    )
    st.sidebar.caption(f"Ordner: {selected_key}")
    return (creator_mode, selected_key)


def _render_wiki_view_from_query() -> bool:
    selected_page = st.query_params.get("page")
    if not selected_page:
        return False

    apply_sl_parchment_theme()
    st.session_state["current_path"] = str(selected_page)
    st.session_state["dashboard_config_errors"] = utils.validate_dashboard_views()
    header()
    create_sidebar()
    return True


def main() -> None:
    _initialize_wiki_context()

    if _render_wiki_view_from_query():
        return

    if LINKED_WIKI_PAGE_QUERY_PARAM in st.query_params:
        st.session_state["current_path"] = st.session_state["root_path"]

    creator_mode, selected_session_key = _render_session_sidebar()
    session_dir = (
        get_session_dir_by_key(selected_session_key)
        if selected_session_key is not None
        else None
    )
    if creator_mode:
        apply_sl_parchment_theme()
        render_creator_view(
            session_dir=session_dir,
            selected_session_key_state=SESSION_SELECT_KEY,
        )
        return

    render_sl_dashboard(session_dir=session_dir)


if __name__ == "__main__":
    st.set_page_config(
        page_title=_resolve_page_title(),
        page_icon="🎲",
        layout="wide",
    )
    main()
