import streamlit as st
import os
from components import utils
from components.show_file import show_image
from components.database_view import show_database


def header():
    cols = st.columns([5, 1], vertical_alignment="top")
    cols[0].markdown(f":gray-badge[{st.session_state['current_path']}]")
    __search_field(cols[1])
    col = st.columns([1, 15])
    show_image(col[0], "dnd_logo.svg", False)

    if (
        not st.session_state["current_path"].endswith(".md")
        and not st.session_state["db_flag"]
    ):
        st.header(f"{st.session_state['current_path'].split('/')[-1]}")
        name = "Ardanos Wiki"
        st.text(
            """Navigiere mit der Sidebar durch das Wiki und erkunde die Ecken von Andaros. Mit zurück kommst du in den vorherigen Ordner. Viel Spaß und melde dich, wenn du mal wieder eine Runde in diesem Universum spielen willst."""
        )
        cols = st.columns([1, 7])
        show_image(cols[0], "Wappen Drakmora.png")
        show_image(cols[0], "Wappen Elmrath.png")
        show_image(cols[0], "Wappen Mariven.png")
        show_image(cols[0], "Wappen Vaylen.png")
        show_image(cols[0], "Wappen Schwarzklamm.png")
        show_image(cols[1], "Ardanos.jpeg")
    elif st.session_state["db_flag"]:
        show_database(f"{st.session_state['root_path']}/{st.session_state['db']}")
        name = st.session_state["db"]
        st.session_state["db_flag"] = False
    else:
        name = st.session_state["current_path"].split("/")[-1].replace(".md", "")
    name = name.split("_")[-1]
    col[1].title(f":red[{name}]")


def __search_field(st_obj: st):
    all_files = utils.get_all_file_paths(st.session_state["tree"])
    file_names = ["Suche Dokument"]
    file_names.extend([os.path.basename(f).replace(".md", "") for f in all_files])

    selected = st_obj.selectbox(
        "🔍 Suche nach Datei", file_names, key="searchfield", index=0
    )
    if selected != "Suche Dokument":
        # vollständiger Pfad zur Datei finden:
        selected_path = next(
            (p for p in all_files if os.path.basename(p) == f"{selected}.md"), None
        )
        if selected_path:
            st.session_state["current_path"] = selected_path
            st.session_state.pop("searchfield", None)
