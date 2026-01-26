import streamlit as st

from components.show_file import show_file
from config import cfg
from components import utils
from components.login import login_filed
from components.database_view import set_to_databse_view
from components.login import Roles
from components.encounter_calculator import set_to_encounter_calculator_view


def dnd_line(pos: st, label: str, value: str = ""):
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


def create_sidebar():
    st.logo(f"{cfg.IMAGE_DIR}/dnd_logo.svg", size="large")
    st.sidebar.header("🧭 Navigation")
    col = st.sidebar.columns(2)
    col[0].button("Zurück", on_click=utils.go_on_top_folder)
    col[1].button("Home", on_click=utils.go_to_root)
    login_filed(st.sidebar)

    if st.session_state["current_path"].endswith(".md"):
        show_file(st.session_state["current_path"])
        if any(
            [folder in st.session_state["current_path"] for folder in cfg.DATABASE_LIST]
        ):
            st.session_state["current_path"] = "/".join(
                st.session_state["current_path"].split("/")[:-2]
            )

    subtree = utils.get_subtree_by_path(st.session_state["current_path"])
    if not subtree:
        st.stop()

    name = st.session_state["current_path"].split("/")[-1].replace(".md", "")
    dnd_line(st.sidebar, name)

    i = 1
    for folder in subtree:
        if folder == "__files__" or any([f in folder for f in cfg.DATABASE_LIST]):
            continue
        st.sidebar.button(
            f"{i}. {utils.format_path(folder)}",
            key=folder,
            use_container_width=True,
            type="tertiary",
            on_click=utils.go_to_folder,
            args=(folder,),
        )
        i += 1

    if st.session_state["current_path"] == st.session_state["root_path"]:
        dnd_line(st.sidebar, "Sammlungen:")
        for db in cfg.DATABASE_LIST:
            # show bestiarium only for the gamemaster
            if (
                db == "Bestiarium"
                and st.session_state["user"].role.value != Roles.GameMaster.value
            ):
                continue

            st.sidebar.button(
                db,
                key=f"{db}_view",
                use_container_width=True,
                type="tertiary",
                on_click=set_to_databse_view,
                args=(db,),
            )
        for feat in cfg.SPECIAL_FEATURE:
            st.sidebar.button(
                feat,
                key=f"{feat}_view",
                use_container_width=True,
                type="tertiary",
                on_click=set_to_encounter_calculator_view,
            )

    if "__files__" in subtree:
        dnd_line(st.sidebar, "Seiten:")
        for file in subtree["__files__"]:
            st.sidebar.button(
                utils.format_path(file),
                key=file,
                use_container_width=True,
                type="tertiary",
                on_click=utils.set_path,
                args=(file,),
            )
