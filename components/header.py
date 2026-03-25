import streamlit as st
import os
from html import escape
from components import utils
from components.show_file import show_image
from components.dashboard import render_dashboard
from components.database_view import show_database
from components.encounter_calculator import encounter_calculator_view
from components.monster_creator import (
    MONSTER_CREATOR_FEATURE_NAME,
    monster_creator_view,
)
from components.npc_creator import npc_creator_view, NPC_CREATOR_FEATURE_NAME
from config import cfg


def header():
    cols = st.columns([5, 1], vertical_alignment="top")
    apply_breadcrumb_styles()
    render_breadcrumbs(cols[0])
    __search_field(cols[1])
    col = st.columns([1, 15])
    show_image(col[0], "dnd_logo.svg", False)

    if (
        not st.session_state["current_path"].endswith(".md")
        and not st.session_state["db_flag"]
    ):
        st.header(f"{st.session_state['current_path'].split('/')[-1]}")
        name = "Ardanos Wiki"
        dashboard_config_errors = st.session_state.get("dashboard_config_errors", [])
        if dashboard_config_errors:
            st.error(
                "Dashboard-Konfiguration fehlerhaft:\n- "
                + "\n- ".join(dashboard_config_errors)
            )
        dashboard_view = utils.resolve_dashboard_view(st.session_state["current_path"])
        render_dashboard(dashboard_view)
    elif st.session_state["db_flag"]:
        name = st.session_state["db"]
        st.session_state["db_flag"] = False
        if any([db in st.session_state["db"] for db in cfg.DATABASE_LIST]):
            show_database(f"{st.session_state['root_path']}/{st.session_state['db']}")
        elif any([db in st.session_state["db"] for db in cfg.SPECIAL_FEATURE]):
            if st.session_state["db"] == NPC_CREATOR_FEATURE_NAME:
                npc_creator_view()
            elif st.session_state["db"] == MONSTER_CREATOR_FEATURE_NAME:
                monster_creator_view()
            else:
                encounter_calculator_view()

    else:
        name = st.session_state["current_path"].split("/")[-1].replace(".md", "")
    name = name.split("_")[-1]
    col[1].title(f":red[{name}]")


def apply_breadcrumb_styles() -> None:
    st.markdown(
        """
        <style>
        .app-breadcrumbs {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0;
            padding-top: 0.1rem;
            line-height: 1.2;
        }

        .app-breadcrumbs form {
            display: inline;
            margin: 0;
        }

        .app-breadcrumbs__prefix,
        .app-breadcrumbs__current,
        .app-breadcrumbs__sep,
        .app-breadcrumbs__button {
            white-space: nowrap;
            font-size: 0.95rem;
            line-height: 1.2;
            margin: 0;
            padding: 0;
        }

        .app-breadcrumbs__prefix {
            color: #8b7355;
            font-weight: 600;
            margin-right: 0.25rem;
        }

        .app-breadcrumbs__button {
            display: inline;
            background: transparent;
            border: none;
            color: #5b4636;
            font-weight: 600;
            cursor: pointer;
        }

        .app-breadcrumbs__current {
            color: #7c2d12;
            font-weight: 700;
        }

        .app-breadcrumbs__sep {
            color: #b08968;
            font-weight: 600;
            margin: 0 0.28rem;
        }

        .app-breadcrumbs button:focus {
            outline: none;
            box-shadow: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_breadcrumbs(place) -> None:
    breadcrumb_paths = utils.get_breadcrumb_paths(st.session_state["current_path"])
    breadcrumb_parts = [
        '<div class="app-breadcrumbs">',
        '<span class="app-breadcrumbs__prefix">Pfad:</span>',
    ]

    for index, crumb_path in enumerate(breadcrumb_paths):
        label = (
            "Home"
            if crumb_path == st.session_state["root_path"]
            else utils.format_path(crumb_path)
        )
        escaped_label = escape(label)
        escaped_path = escape(crumb_path)

        if crumb_path == st.session_state["current_path"]:
            breadcrumb_parts.append(
                '<span class="app-breadcrumbs__current">' f"{escaped_label}</span>"
            )
        else:
            breadcrumb_parts.append(
                '<form method="get">'
                f'<input type="hidden" name="page" value="{escaped_path}">'
                '<button class="app-breadcrumbs__button" type="submit">'
                f"{escaped_label}</button></form>"
            )

        if index < len(breadcrumb_paths) - 1:
            breadcrumb_parts.append('<span class="app-breadcrumbs__sep">›</span>')

    breadcrumb_parts.append("</div>")
    place.markdown("".join(breadcrumb_parts), unsafe_allow_html=True)


def __search_field(st_obj):
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
            utils.set_path(selected_path)
            st.session_state.pop("searchfield", None)
