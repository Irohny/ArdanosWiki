import streamlit as st

from components.show_file import show_file
from config import cfg
from components import utils
from components.login import login_filed
from components.database_view import set_to_databse_view
from components.login import Roles
from components.encounter_calculator import set_to_encounter_calculator_view


def dnd_line(pos, label: str, value: str = ""):
    pos.markdown(
        f"""
        <div style="
            display:flex;
            align-items:center;
            font-family: serif;
            margin-bottom:6px;
        ">
            <span style="white-space:nowrap; margin-right:10px;">
                <b>{label}</b> {value}
            </span>
            <div style="
                flex-grow:1;
                border-bottom:2px solid #5b4636;
            "></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_sidebar_button_styles() -> None:
    st.sidebar.markdown(
        """
        <style>
        section[data-testid="stSidebar"] button[kind="tertiary"] {
            justify-content: flex-start;
        }

        section[data-testid="stSidebar"] button[kind="tertiary"] p {
            text-align: left;
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_nav_actions() -> None:
    col = st.sidebar.columns(2)
    col[0].button("Zurück", on_click=utils.go_on_top_folder, use_container_width=True)
    col[1].button("Home", on_click=utils.go_to_root, use_container_width=True)


def render_child_folders(subtree: dict) -> None:
    folders = [
        folder
        for folder in subtree
        if folder != "__files__" and not any(db in folder for db in cfg.DATABASE_LIST)
    ]

    if not folders:
        return

    with st.sidebar.expander("Unterordner", expanded=True):
        for folder in folders:
            st.button(
                f"📁 {utils.format_path(folder)}",
                key=f"folder::{folder}",
                use_container_width=True,
                type="tertiary",
                on_click=utils.go_to_folder,
                args=(folder,),
            )


def render_files(subtree: dict) -> None:
    files = subtree.get("__files__", [])
    with st.sidebar.expander("Seiten", expanded=True):
        if not files:
            st.caption("Keine Seiten in diesem Ordner.")
            return

        for file in files:
            st.button(
                f"📄 {utils.format_path(file)}",
                key=f"file::{file}",
                use_container_width=True,
                type="tertiary",
                on_click=utils.set_path,
                args=(file,),
            )


def render_home_shortcuts() -> None:
    if st.session_state["current_path"] != st.session_state["root_path"]:
        return

    for db in cfg.DATABASE_LIST:
        if (
            db == "Bestiarium"
            and st.session_state["user"].role.value != Roles.GameMaster.value
        ):
            continue

        st.sidebar.button(
            f"📚 {db}",
            key=f"{db}_view",
            use_container_width=True,
            type="tertiary",
            on_click=set_to_databse_view,
            args=(db,),
        )

    for feat in cfg.SPECIAL_FEATURE:
        st.sidebar.button(
            f"🛠️ {feat}",
            key=f"{feat}_view",
            use_container_width=True,
            type="tertiary",
            on_click=set_to_encounter_calculator_view,
        )


def create_sidebar():
    st.logo(f"{cfg.IMAGE_DIR}/dnd_logo.svg", size="large")
    apply_sidebar_button_styles()
    render_nav_actions()
    with st.sidebar.expander("Login", expanded=False):
        login_filed(st)
    render_home_shortcuts()

    if st.session_state["current_path"].endswith(".md"):
        show_file(st.session_state["current_path"])
        if any(
            [folder in st.session_state["current_path"] for folder in cfg.DATABASE_LIST]
        ):
            utils.set_path("/".join(st.session_state["current_path"].split("/")[:-2]))

    subtree = utils.get_subtree_by_path(st.session_state["current_path"])
    if not subtree:
        st.stop()

    name = st.session_state["current_path"].split("/")[-1].replace(".md", "")
    dnd_line(st.sidebar, name)
    render_child_folders(subtree)
    render_files(subtree)
