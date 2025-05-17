import streamlit as st
from pathlib import Path
import os

MARKDOWN_DIR = Path("World/Ardanos")
IMAGE_DIR = Path("World/Images")


def find_markdown_files(folder_path: str) -> dict:
    def build_tree(current_path: str) -> dict:
        tree = {}
        try:
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    subtree = build_tree(item_path)
                    if subtree:  # nur hinzufügen, wenn es Markdown-Dateien enthält
                        tree[item_path] = subtree
                elif item.endswith(".md"):
                    if "__files__" not in tree:
                        tree["__files__"] = []
                    tree["__files__"].append(item_path)
        except PermissionError:
            pass  # überspringt Ordner ohne Zugriffsrechte
        return tree

    abs_root = os.path.abspath(folder_path)
    return {abs_root: build_tree(abs_root)}


def get_subtree_by_path(target_path: str):
    """
    Navigiert durch ein Tree-Dictionary bis zum target_path relativ zu root_path.
    Gibt das entsprechende Subtree-Dict zurück oder None, wenn Pfad nicht gefunden.
    """
    root_path = os.path.abspath(st.session_state["root_path"])
    target_path = os.path.abspath(target_path)
    if root_path not in st.session_state["tree"]:
        return None

    current = st.session_state["tree"][os.path.abspath(st.session_state["root_path"])]

    if target_path == root_path:
        return current

    target_path = os.path.abspath(target_path)
    segments = os.path.relpath(target_path, root_path).split(os.sep)
    path = root_path
    for segment in segments:
        path = f"{path}/{segment}"
        current = current[path]
    return current


def create_sidebar():
    st.sidebar.title("🧭 Navigation")
    st.sidebar.button("Zurück", on_click=go_on_top_folder)
    i = 1
    subtree = get_subtree_by_path(st.session_state["current_path"])
    if not subtree:
        st.stop()

    for folder in subtree:
        if folder == "__files__":
            continue
        st.sidebar.button(
            f"{i}. {format_path(folder)}",
            key=folder,
            use_container_width=True,
            type="tertiary",
            on_click=go_to_folder,
            args=(folder,),
        )
        i += 1

    st.sidebar.markdown("---")
    if "__files__" in subtree:
        for file in subtree["__files__"]:
            st.sidebar.button(
                format_path(file),
                key=file,
                use_container_width=True,
                type="tertiary",
                on_click=show_file,
                args=(file,),
            )


def main():
    create_sidebar()
    st.title("D&D Kampagnen-Wiki")


def show_file(file_path: str):
    """Liest eine Markdown-Datei ein und zeigt den Inhalt in Streamlit an."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            st.markdown(content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Datei nicht gefunden: `{file_path}`")
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei `{file_path}`: {e}")


def format_path(path):
    return str(path).split("/")[-1].replace(".md", "")


def go_to_folder(folder):
    st.session_state["current_path"] = folder


def go_on_top_folder():
    root_path = os.path.abspath(st.session_state["root_path"])
    target_path = os.path.abspath(st.session_state["current_path"])
    if target_path == root_path:
        st.session_state["current_path"] = root_path
    parts = str(target_path).split("/")
    new_path = "/".join(part for part in parts[:-1])
    print(new_path)
    st.session_state["current_path"] = new_path


if __name__ == "__main__":
    st.session_state["tree"] = find_markdown_files(MARKDOWN_DIR)
    if "root_path" not in st.session_state:
        st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["current_path"] = str(list(st.session_state["tree"].keys())[0])

    main()
