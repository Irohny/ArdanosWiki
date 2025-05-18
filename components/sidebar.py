import streamlit as st
from components import utils


def create_sidebar():
    st.sidebar.title("🧭 Navigation")
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


def show_file(file_path: str):
    """Liest eine Markdown-Datei ein und zeigt den Inhalt in Streamlit an."""
    try:
        title = (file_path.split("/")[-1]).replace(".md", "")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            st.title(title)
            st.markdown(content, unsafe_allow_html=True)
            st.session_state["current_path"] = file_path
    except FileNotFoundError:
        st.error(f"Datei nicht gefunden: `{file_path}`")
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei `{file_path}`: {e}")
