import streamlit as st

from wiki_dasboard.components.access_control import campaigns_for_user
from wiki_dasboard.components.show_file import show_file
from wiki_dasboard.config import cfg
from wiki_dasboard.components import utils
from wiki_dasboard.components.login import login_filed
from wiki_dasboard.components.database_view import set_to_databse_view
from wiki_dasboard.components.login import Roles
from wiki_dasboard.components.toolbox import set_to_toolbox_view
from wiki_dasboard.components.dashboard import CAMPAIGN_OVERVIEW_EXPANDED_KEY
from wiki_dasboard.components.interactive_map import ARDANOS_MAP_OPEN_KEY


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


def _apply_campaign_selection() -> None:
    user = st.session_state["user"]
    selected_id = st.session_state.get("wiki_campaign_selector")
    campaigns = dict(campaigns_for_user(user, cfg.paths.world_dir))
    if selected_id is not None and selected_id not in campaigns:
        return

    tree = utils.find_markdown_files(
        str(cfg.paths.world_dir), user, campaign_id=selected_id
    )
    st.session_state.pop(CAMPAIGN_OVERVIEW_EXPANDED_KEY, None)
    root_path = next(iter(tree))
    st.session_state["active_campaign_id"] = selected_id
    st.session_state["tree"] = tree
    st.session_state["root_path"] = root_path
    st.session_state["current_path"] = root_path
    if selected_id is None:
        st.session_state.pop("campaign_overview_mode", None)
    st.session_state["db_flag"] = False
    st.session_state["db"] = ""
    st.query_params.pop("page", None)
    st.query_params.pop(utils.DATABASE_VIEW_QUERY_PARAM, None)
    st.query_params.pop(utils.WIKI_DIALOG_QUERY_PARAM, None)


def _open_campaign_overview() -> None:
    root_path = st.session_state["root_path"]
    st.session_state["current_path"] = root_path
    st.session_state["campaign_overview_mode"] = True
    st.session_state.pop(CAMPAIGN_OVERVIEW_EXPANDED_KEY, None)
    st.session_state["db_flag"] = False
    st.session_state["db"] = ""
    st.query_params.pop("page", None)
    st.query_params.pop(utils.DATABASE_VIEW_QUERY_PARAM, None)
    st.query_params.pop(utils.WIKI_DIALOG_QUERY_PARAM, None)


def _open_ardanos_map() -> None:
    st.session_state[ARDANOS_MAP_OPEN_KEY] = True
    st.session_state["db_flag"] = False
    st.session_state["db"] = ""
    st.session_state.pop("campaign_overview_mode", None)
    st.session_state.pop(CAMPAIGN_OVERVIEW_EXPANDED_KEY, None)
    st.query_params.pop("page", None)
    st.query_params.pop(utils.DATABASE_VIEW_QUERY_PARAM, None)
    st.query_params.pop(utils.WIKI_DIALOG_QUERY_PARAM, None)


def render_campaign_filter(place, campaigns) -> None:
    if not campaigns:
        return

    labels = dict(campaigns)
    campaign_ids = list(labels)
    active_id = st.session_state.get("active_campaign_id")
    if active_id is not None and active_id not in labels:
        active_id = None
        st.session_state["active_campaign_id"] = active_id
        st.session_state["wiki_campaign_selector"] = active_id
        _apply_campaign_selection()
    elif st.session_state.get("wiki_campaign_selector") != active_id:
        st.session_state["wiki_campaign_selector"] = active_id

    place.selectbox(
        "Kampagne",
        options=[None, *campaign_ids],
        format_func=lambda campaign_id: (
            "Alle Seiten" if campaign_id is None else labels[campaign_id]
        ),
        key="wiki_campaign_selector",
        on_change=_apply_campaign_selection,
    )


def render_campaign_navigation() -> None:
    user = st.session_state["user"]
    if user.role.value != Roles.Player.value:
        return

    campaigns = campaigns_for_user(user, cfg.paths.world_dir)
    if not campaigns:
        return

    active_id = st.session_state.get("active_campaign_id")
    if active_id is None:
        return

    st.sidebar.button(
        "Kampagnenübersicht",
        key="campaign_overview_button",
        use_container_width=True,
        type="tertiary",
        on_click=_open_campaign_overview,
    )


def render_child_folders(subtree: dict) -> None:
    folders = [
        folder
        for folder in subtree
        if folder != "__files__"
        and not any(db in folder for db in cfg.navigation.databases)
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
    is_home = st.session_state["current_path"] == st.session_state["root_path"]
    is_game_master = st.session_state["user"].role.value == Roles.GameMaster.value
    expander = st.sidebar.expander("Sammlungen", expanded=False)
    if is_home:
        expander.button(
            "Karte von Ardanos",
            key="ardanos_map_view",
            use_container_width=True,
            type="tertiary",
            on_click=_open_ardanos_map,
        )
        for db in cfg.navigation.databases:
            if db == "Bestiarium" and not is_game_master:
                continue

            expander.button(
                f"📚 {db}",
                key=f"{db}_view",
                use_container_width=True,
                type="tertiary",
                on_click=set_to_databse_view,
                args=(db,),
            )

    for feat in cfg.features.special_features:
        if not is_game_master:
            continue

        expander.button(
            f"🛠️ {feat}",
            key=f"{feat}_view",
            use_container_width=True,
            type="tertiary",
            on_click=set_to_toolbox_view,
        )


def create_sidebar():
    st.logo(f"{cfg.paths.image_dir}/dnd_logo.svg", size="large")
    apply_sidebar_button_styles()
    render_nav_actions()
    with st.sidebar.expander("Login", expanded=False):
        login_filed(st)
    render_home_shortcuts()
    render_campaign_navigation()

    if st.session_state["current_path"].endswith(".md"):
        show_file(st.session_state["current_path"])
        if any(
            [
                folder in st.session_state["current_path"]
                for folder in cfg.navigation.databases
            ]
        ):
            utils.set_path("/".join(st.session_state["current_path"].split("/")[:-2]))

    subtree = utils.get_subtree_by_path(st.session_state["current_path"])
    if not subtree:
        st.stop()

    name = utils.format_path(st.session_state["current_path"])
    dnd_line(st.sidebar, name)
    render_child_folders(subtree)
    render_files(subtree)
