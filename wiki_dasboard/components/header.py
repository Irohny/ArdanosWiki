import streamlit as st
from html import escape
from wiki_dasboard.components import utils
from wiki_dasboard.components.show_file import show_image
from wiki_dasboard.components.dashboard import (
    render_campaign_overview,
    render_dashboard,
)
from wiki_dasboard.components.database_view import show_database
from wiki_dasboard.components.toolbox import toolbox_view
from wiki_dasboard.components.access_control import campaigns_for_user
from wiki_dasboard.components.login import Roles
from wiki_dasboard.components.sidebar import render_campaign_filter
from wiki_dasboard.components.interactive_map import (
    ARDANOS_MAP_OPEN_KEY,
    render_interactive_map,
)
from wiki_dasboard.config import cfg


def header():
    user = st.session_state.get("user")
    campaigns = (
        campaigns_for_user(user, cfg.paths.world_dir)
        if user and user.role.value == Roles.Player.value
        else []
    )
    cols = st.columns(
        [5, 1.2, 1.2] if campaigns else [5, 1],
        vertical_alignment="top",
    )
    apply_breadcrumb_styles()
    render_breadcrumbs(cols[0])
    if campaigns:
        render_campaign_filter(cols[1], campaigns)
        __search_field(cols[2])
    else:
        __search_field(cols[1])
    col = st.columns([1, 15])
    show_image(col[0], "dnd_logo.svg", False)

    user = st.session_state.get("user")
    active_campaign_id = st.session_state.get("active_campaign_id")
    player_context = bool(user and user.role.value == "Player")
    player_campaign_context = (
        player_context
        and active_campaign_id in cfg.player_access.campaign_labels
    )
    is_campaign_home = (
        player_campaign_context
        and st.session_state["current_path"] == st.session_state["root_path"]
    )

    campaign_overview = st.session_state.get("campaign_overview_mode", False)
    map_open = st.session_state.get(ARDANOS_MAP_OPEN_KEY, False)

    if map_open:
        name = "Karte von Ardanos"
    elif campaign_overview:
        name = "Kampagnenübersicht"
    elif (
        not st.session_state["current_path"].endswith(".md")
        and not st.session_state["db_flag"]
    ):
        if player_campaign_context:
            name = (
                cfg.player_access.campaign_labels[active_campaign_id]
                if is_campaign_home
                else utils.format_path(st.session_state["current_path"])
            )
            dashboard_view = utils.resolve_dashboard_view(
                st.session_state["current_path"]
            )
            render_dashboard(dashboard_view)
        else:
            st.header(f"{utils.format_path(st.session_state['current_path'])}")
            name = "Ardanos Wiki"
            dashboard_config_errors = st.session_state.get(
                "dashboard_config_errors", []
            )
            if dashboard_config_errors:
                st.error(
                    "Dashboard-Konfiguration fehlerhaft:\n- "
                    + "\n- ".join(dashboard_config_errors)
                )
            dashboard_view = utils.resolve_dashboard_view(
                st.session_state["current_path"]
            )
            render_dashboard(dashboard_view)
    elif st.session_state["db_flag"]:
        name = st.session_state["db"]
        st.session_state["db_flag"] = False
        if any(
            db in st.session_state["db"] for db in cfg.navigation.databases
        ):
            show_database(f"{st.session_state['root_path']}/{st.session_state['db']}")
        elif st.session_state["db"] == cfg.features.toolbox_name:
            toolbox_view(show_title=False)

    else:
        name = utils.format_path(st.session_state["current_path"])
    name = name.split("_")[-1]
    col[1].title(f":red[{name}]")
    if map_open:
        render_interactive_map()
    elif campaign_overview:
        render_campaign_overview(st.session_state["tree"])

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
    file_names.extend([utils.format_path(path) for path in all_files])

    selected = st_obj.selectbox(
        "🔍 Suche nach Datei", file_names, key="searchfield", index=0
    )
    if selected != "Suche Dokument":
        # vollständiger Pfad zur Datei finden:
        selected_path = next(
            (path for path in all_files if utils.format_path(path) == selected), None
        )
        if selected_path:
            utils.set_path(selected_path)
            st.session_state.pop("searchfield", None)
