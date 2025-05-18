import streamlit as st
import os


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


def get_subtree_by_path(target_path: str) -> dict:
    """
    Navigiert durch ein Tree-Dictionary bis zum target_path relativ zu root_path.
    Gibt das entsprechende Subtree-Dict zurück oder None, wenn Pfad nicht gefunden.
    """
    root_path = os.path.abspath(st.session_state["root_path"])

    if (target_path.split("/")[-1]).endswith(".md"):
        splits = target_path.split("/")
        target_path = "/".join(split for split in splits[:-1])

    target_path = os.path.abspath(target_path)
    if root_path not in st.session_state["tree"]:
        return st.session_state["tree"]

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


def format_path(path):
    return str(path).split("/")[-1].replace(".md", "")


def go_to_folder(folder):
    st.session_state["current_path"] = folder


def go_on_top_folder():
    root_path = os.path.abspath(st.session_state["root_path"])
    target_path = os.path.abspath(st.session_state["current_path"])
    if target_path == root_path:
        st.session_state["current_path"] = root_path
        return
    parts = str(target_path).split("/")
    new_path = "/".join(part for part in parts[:-1])
    st.session_state["current_path"] = new_path


def find_file_path_in_tree(
    tree: dict, filename: str, current_path: str = ""
) -> str | None:
    """
    Durchsucht rekursiv das Tree-Dictionary nach einer Datei und gibt den vollständigen Pfad zurück.

    :param tree: Das Tree-Dictionary mit Ordnern und Markdown-Dateien
    :param filename: Gesuchter Dateiname (z. B. "beispiel.md")
    :param current_path: Interner Rekursionspfad
    :return: Vollständiger Pfad zur Datei oder None, wenn nicht gefunden
    """
    if not current_path:
        current_path = st.session_state["root_path"]
    for key, value in tree.items():
        if key == "__files__":
            for file in value:
                if filename in file:
                    return os.path.join(current_path, file)
        else:
            # Rekursiv in Unterordnern suchen
            result = find_file_path_in_tree(
                value, filename, os.path.join(current_path, key)
            )
            if result:
                return result
    return None
