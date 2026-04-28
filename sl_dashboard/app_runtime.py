from pathlib import Path

import streamlit as st

from components import utils
from components.header import header
from components.file_parser import build_markdown_database
from components.login import Roles, User
from components.sidebar import create_sidebar
from config import cfg
from sl_dashboard import render_sl_dashboard, render_sl_dashboard_encounter
from sl_dashboard.creator_view import render_creator_view, render_new_session_form
from sl_dashboard.components.markdown import LINKED_WIKI_PAGE_QUERY_PARAM
from sl_dashboard.components.theme import apply_sl_parchment_theme
from sl_dashboard.loader import get_session_dir_by_key, list_available_sessions


SESSION_SELECT_KEY = "sl_dashboard_selected_session"
SHOW_CREATE_SESSION_EXPANDER_KEY = "sl_dashboard_show_create_session_expander"
LEAD_PAGE_PATH = "sl_dashboard_pages/leitungsansicht.py"
ENCOUNTER_PAGE_PATH = "sl_dashboard_pages/kampftracker.py"
WORKSHOP_PAGE_PATH = "sl_dashboard_pages/werkstatt.py"
LEAD_URL_PATH = "leitung"
ENCOUNTER_URL_PATH = "kampftracker"
WORKSHOP_URL_PATH = "werkstatt"


def resolve_page_title() -> str:
    selected_page = st.query_params.get("page")
    if not selected_page:
        return "SL-Dashboard"

    return Path(str(selected_page)).stem


def initialize_wiki_context() -> None:
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


def render_session_selector(selected_page_url_path: str) -> Path | None:
    session_options = list_available_sessions()
    is_workshop_page = selected_page_url_path == WORKSHOP_URL_PATH

    option_keys = [option.key for option in session_options]
    selected_key = None

    if is_workshop_page:
        selector_col, button_col, _ = st.columns((1, 0.45, 2.55), gap="small")
    else:
        selector_col, _ = st.columns((1, 3), gap="large")
        button_col = None

    with selector_col:
        if option_keys:
            default_key = st.session_state.get(SESSION_SELECT_KEY)
            if default_key not in option_keys:
                default_key = session_options[0].key
                st.session_state[SESSION_SELECT_KEY] = default_key

            selected_key = st.selectbox(
                "Aktive Session",
                option_keys,
                key=SESSION_SELECT_KEY,
                format_func=lambda key: next(
                    option.title for option in session_options if option.key == key
                ),
            )
        elif is_workshop_page:
            st.caption("Noch keine Session vorhanden.")
        else:
            st.caption("Keine Session-Daten gefunden.")

    if button_col is not None:
        with button_col:
            if st.button(
                "Neue Session",
                key="sl_create_session_toggle",
                use_container_width=True,
            ):
                current_state = bool(
                    st.session_state.get(SHOW_CREATE_SESSION_EXPANDER_KEY, False)
                )
                st.session_state[SHOW_CREATE_SESSION_EXPANDER_KEY] = not current_state

        if st.session_state.get(SHOW_CREATE_SESSION_EXPANDER_KEY, False):
            with st.expander("Neue Session", expanded=True):
                render_new_session_form(
                    SESSION_SELECT_KEY,
                    form_key_suffix="top-expander",
                    close_state_key=SHOW_CREATE_SESSION_EXPANDER_KEY,
                )

    if selected_key is None:
        return None
    return get_session_dir_by_key(selected_key)


def render_wiki_view_from_query() -> bool:
    selected_page = st.query_params.get("page")
    if not selected_page:
        return False

    apply_sl_parchment_theme()
    st.session_state["current_path"] = str(selected_page)
    st.session_state["dashboard_config_errors"] = utils.validate_dashboard_views()
    header()
    create_sidebar()
    return True


def build_dashboard_pages() -> list:
    return [
        st.Page(
            LEAD_PAGE_PATH,
            title="Leitungsansicht",
            icon="🎲",
            url_path=LEAD_URL_PATH,
            default=True,
        ),
        st.Page(
            ENCOUNTER_PAGE_PATH,
            title="Kampftracker",
            icon="⚔️",
            url_path=ENCOUNTER_URL_PATH,
        ),
        st.Page(
            WORKSHOP_PAGE_PATH,
            title="Werkstatt",
            icon="🛠️",
            url_path=WORKSHOP_URL_PATH,
        ),
    ]


def prepare_dashboard_navigation():
    initialize_wiki_context()

    if render_wiki_view_from_query():
        return None

    if LINKED_WIKI_PAGE_QUERY_PARAM in st.query_params:
        st.session_state["current_path"] = st.session_state["root_path"]

    return st.navigation(build_dashboard_pages(), position="top")


def render_lead_page() -> None:
    session_dir = render_session_selector(LEAD_URL_PATH)
    render_sl_dashboard(session_dir=session_dir)


def render_encounter_page() -> None:
    session_dir = render_session_selector(ENCOUNTER_URL_PATH)
    render_sl_dashboard_encounter(session_dir=session_dir)


def render_workshop_page() -> None:
    apply_sl_parchment_theme()
    session_dir = render_session_selector(WORKSHOP_URL_PATH)
    render_creator_view(
        session_dir=session_dir,
        selected_session_key_state=SESSION_SELECT_KEY,
    )