import streamlit as st
import os
from components.login import User, Roles
from config import DashboardViewConfig, cfg
from collections import Counter
from pathlib import Path


def collect_images_by_name(root_path: str) -> dict[str, str]:
    """
    Durchsucht rekursiv root_path nach Bildern und gibt ein Dict
    {bildname: voller_pfad} zurück.
    """
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
    images = {}

    root = Path(root_path)

    for file in root.rglob("*"):
        if file.is_file() and file.suffix.lower() in image_extensions:
            images[file.name] = str(file.resolve())

    return images


def has_permission(path: str | None, user: User) -> bool:
    if path is None:
        return True
    file = path.split("/")[-1]
    if user.role.value == Roles.GameMaster.value:  # dm can see all files
        return True
    elif file == "Spielleiter":  # skip dm files if not dm
        return False
    elif "_" not in file:  # show all files without permissions
        return True
    elif user.role.value == Roles.Player.value:
        return file.startswith(cfg.ROLE_MAPPING[user.name])
    return False


def find_markdown_files(folder_path: str, user: User) -> dict:
    def build_tree(current_path: str) -> dict:
        tree = {}
        try:
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if any([ignore in item_path for ignore in cfg.IGNORE_LIST]):
                    continue
                if not has_permission(item_path, user):
                    continue

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


@st.cache_data
def get_all_file_paths(tree):
    """Gibt eine Liste aller Markdown-Dateipfade im Tree zurück."""
    paths = []

    def collect(subtree, current_path=""):
        for key, value in subtree.items():
            if key == "__files__":
                for f in value:
                    paths.append(os.path.join(current_path, f))
            elif isinstance(value, dict):
                collect(value, os.path.join(current_path, key))

    collect(tree)
    return paths


@st.cache_data
def get_all_folder_paths(tree):
    """Gibt eine Liste aller sichtbaren Ordnerpfade im Tree zurück."""
    paths = []

    def collect(subtree):
        for key, value in subtree.items():
            if key == "__files__":
                continue
            paths.append(key)
            if isinstance(value, dict):
                collect(value)

    collect(tree)
    return paths


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


def format_relative_path(path: str) -> str:
    relative_path = relative_path_from_root(path)
    if not relative_path:
        return format_path(path)
    return relative_path.replace(".md", "")


def sync_current_path(path: str) -> None:
    st.session_state["current_path"] = path
    st.query_params["page"] = path


def go_to_folder(folder):
    sync_current_path(folder)


def go_to_root():
    go_to_folder(st.session_state["root_path"])


def go_on_top_folder():
    root_path = os.path.abspath(st.session_state["root_path"])
    target_path = os.path.abspath(st.session_state["current_path"])
    if target_path == root_path:
        sync_current_path(root_path)
        return
    parts = str(target_path).split("/")
    new_path = "/".join(part for part in parts[:-1])
    sync_current_path(new_path)


def set_path(path: str):
    sync_current_path(path)


def get_breadcrumb_paths(path: str) -> list[str]:
    root_path = Path(st.session_state["root_path"]).resolve()
    current_path = Path(path).resolve()

    breadcrumb_paths = [str(root_path)]

    if current_path.suffix == ".md":
        folder_path = current_path.parent
        include_file = True
    else:
        folder_path = current_path
        include_file = False

    try:
        relative_parts = folder_path.relative_to(root_path).parts
    except ValueError:
        return breadcrumb_paths

    running_path = root_path
    for part in relative_parts:
        running_path = running_path / part
        breadcrumb_paths.append(str(running_path))

    if include_file:
        breadcrumb_paths.append(str(current_path))

    return breadcrumb_paths


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


def relative_path_from_root(path: str) -> str:
    root_path = Path(st.session_state["root_path"]).resolve()
    current_path = Path(path).resolve()

    if current_path.suffix == ".md":
        current_path = current_path.parent

    try:
        relative_path = current_path.relative_to(root_path)
    except ValueError:
        return ""

    return relative_path.as_posix()


def resolve_dashboard_view(path: str) -> DashboardViewConfig | None:
    relative_path = relative_path_from_root(path)
    for view in cfg.DASHBOARD_VIEWS:
        if relative_path == view.path_prefix or relative_path.startswith(
            f"{view.path_prefix}/"
        ):
            return view
    return None


def resolve_dashboard_asset_path(view: DashboardViewConfig) -> Path | None:
    if view.asset_path is None:
        return None

    asset_path = Path(view.asset_path)
    if not asset_path.is_absolute():
        asset_path = cfg.REPO_ROOT / asset_path

    resolved_path = asset_path.resolve()
    if not resolved_path.exists() or not resolved_path.is_file():
        return None
    return resolved_path


def validate_dashboard_views() -> list[str]:
    errors: list[str] = []
    allowed_modes = {"default", "timeline"}

    prefix_counter = Counter(view.path_prefix for view in cfg.DASHBOARD_VIEWS)
    duplicate_prefixes = sorted(
        prefix for prefix, count in prefix_counter.items() if count > 1
    )
    for prefix in duplicate_prefixes:
        errors.append(f"Dashboard path_prefix mehrfach definiert: {prefix}")

    key_counter = Counter(view.key for view in cfg.DASHBOARD_VIEWS)
    duplicate_keys = sorted(key for key, count in key_counter.items() if count > 1)
    for key in duplicate_keys:
        errors.append(f"Dashboard key mehrfach definiert: {key}")

    for view in cfg.DASHBOARD_VIEWS:
        if view.mode not in allowed_modes:
            errors.append(
                f"Dashboard {view.key} verwendet unbekannten mode: {view.mode}"
            )

        if view.layout_columns is not None:
            if len(view.layout_columns) != 3 or any(
                value <= 0 for value in view.layout_columns
            ):
                errors.append(
                    f"Dashboard {view.key} hat ungueltige layout_columns: {view.layout_columns}"
                )

        if view.mode != "timeline":
            continue

        if view.asset_path is None:
            errors.append(f"Dashboard {view.key} fehlt asset_path fuer Timeline-Modus")
            continue

        if resolve_dashboard_asset_path(view) is None:
            errors.append(
                f"Dashboard {view.key} referenziert fehlendes Asset: {view.asset_path}"
            )

    return errors
