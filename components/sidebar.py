import streamlit as st

from components.show_file import show_file
from config import cfg
from components import utils


def create_sidebar():
    st.logo(f"{cfg.IMAGE_DIR}/dnd_logo.svg", size="large")
    st.sidebar.header("🧭 Navigation")
    st.sidebar.button("Zurück", on_click=utils.go_on_top_folder)

    subtree = utils.get_subtree_by_path(st.session_state["current_path"])
    if not subtree:
        st.stop()

    st.sidebar.markdown("---")
    i = 1
    for folder in subtree:
        if folder == "__files__":
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

    if i > 1:
        st.sidebar.markdown("---")

    if "__files__" in subtree:
        for file in subtree["__files__"]:
            st.sidebar.button(
                utils.format_path(file),
                key=file,
                use_container_width=True,
                type="tertiary",
                on_click=show_file,
                args=(file,),
            )
