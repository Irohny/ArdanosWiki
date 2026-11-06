from pathlib import Path
import sys
from urllib.parse import urlencode
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wiki_dasboard.components.auth import clear_auth_cookie, load_auth_claims_from_cookie, lookup_user_record  # noqa: E402
from wiki_dasboard.components.sidebar import create_sidebar  # noqa: E402
from wiki_dasboard.components.header import header  # noqa: E402
from wiki_dasboard.components import utils  # noqa: E402
from wiki_dasboard.config import cfg  # noqa: E402
from wiki_dasboard.components.login import Roles, User, login_filed  # noqa: E402
from wiki_dasboard.components.file_parser import build_markdown_database  # noqa: E402
from wiki_dasboard.components.show_file import WIKI_DIALOG_QUERY_PARAM, show_file  # noqa: E402
from wiki_dasboard.components.utils import DATABASE_VIEW_QUERY_PARAM  # noqa: E402
from wiki_dasboard.components.interactive_map import MAP_PENDING_DIALOG_KEY  # noqa: E402


@st.dialog("Verlinkte Wiki-Seite", width="large")
def render_wiki_dialog(file_path: str) -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] > div {
            justify-content: flex-end !important;
            align-items: stretch !important;
        }
        div[data-testid="stDialog"] div[role="dialog"] {
            width: min(48rem, 100vw) !important;
            height: 100vh !important;
            max-height: 100vh !important;
            margin: 0 !important;
            border-radius: 0 !important;
            overflow-y: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([5, 1])
    cols[0].subheader(Path(file_path).stem)
    cols[1].link_button(
        "->",
        "?" + urlencode({"page": file_path}),
        help="Als Hauptseite öffnen",
        type="tertiary",
    )
    show_file(file_path)


def restore_persisted_user() -> User | None:
    claims = load_auth_claims_from_cookie()
    if claims is None:
        return None

    user_record = lookup_user_record(claims["name"])
    if user_record is None:
        clear_auth_cookie()
        return None

    expected_role = str(user_record.get("role", Roles.Default.value)).strip()
    if claims["role"] != expected_role:
        clear_auth_cookie()
        return None

    return User(
        name=str(user_record.get("name", "")).strip() or claims["name"],
        user_name=str(user_record.get("user_name", claims["name"])).strip(),
        role=Roles(expected_role),
        loged_in=True,
        character_ids=user_record.get("characters", user_record.get("charakter")),
        campaigns=user_record.get("campaigns"),
    )


def ensure_app_user() -> User:
    user = st.session_state.get("user")
    if isinstance(user, User) and user.loged_in:
        return user
    if isinstance(user, User) and st.session_state.get("auth_cookie_clear_pending"):
        return user

    restored_user = restore_persisted_user()
    if restored_user is not None:
        st.session_state["user"] = restored_user
        return restored_user

    if isinstance(user, User):
        return user

    st.session_state["user"] = User()
    return st.session_state["user"]


def render_login_screen() -> None:
    _, content_col, _ = st.columns((1, 1.2, 1), gap="large")
    with content_col:
        st.title("Login")
        st.caption("Melde dich an, um die Wiki-App zu nutzen.")
        with st.container(border=True):
            login_filed(st)


def main():
    requested_page = st.query_params.get("page")
    if requested_page:
        visible_navigation_paths = {
            Path(path).resolve()
            for path in (
                *utils.get_all_file_paths(st.session_state["tree"]),
                *utils.get_all_folder_paths(st.session_state["tree"]),
            )
        }
        if Path(str(requested_page)).resolve() in visible_navigation_paths:
            st.session_state["current_path"] = str(requested_page)
        else:
            st.session_state["current_path"] = st.session_state["root_path"]
            st.query_params.pop("page", None)

    database_view = st.query_params.get(DATABASE_VIEW_QUERY_PARAM)
    if database_view in cfg.navigation.databases:
        is_game_master = (
            st.session_state["user"].role.value == Roles.GameMaster.value
        )
        if database_view == "Bestiarium" and not is_game_master:
            st.query_params.pop(DATABASE_VIEW_QUERY_PARAM, None)
            st.session_state["db"] = ""
            st.session_state["db_flag"] = False
        else:
            st.session_state["db"] = database_view
            st.session_state["db_flag"] = True
    elif database_view:
        st.query_params.pop(DATABASE_VIEW_QUERY_PARAM, None)
    header()
    create_sidebar()
    linked_page = st.session_state.pop(MAP_PENDING_DIALOG_KEY, None)
    if linked_page is None:
        linked_page = st.query_params.get(WIKI_DIALOG_QUERY_PARAM)
    if linked_page:
        linked_page = str(linked_page)
        if linked_page in utils.get_all_file_paths(st.session_state["tree"]):
            st.query_params.pop(WIKI_DIALOG_QUERY_PARAM, None)
            render_wiki_dialog(linked_page)
        else:
            st.query_params.pop(WIKI_DIALOG_QUERY_PARAM, None)


if __name__ == "__main__":
    st.set_page_config(
        "DnD Wiki", page_icon=f"{cfg.paths.image_dir}/dnd_logo.svg", layout="wide"
    )
    user = ensure_app_user()
    if not user.loged_in:
        render_login_screen()
        st.stop()

    if "root_path" not in st.session_state:
        st.session_state["active_campaign_id"] = None
        st.session_state["wiki_campaign_selector"] = None
        st.session_state["tree"] = utils.find_markdown_files(
            cfg.paths.world_dir,
            st.session_state["user"],
        )
        st.session_state["images"] = utils.collect_images_by_name(
            cfg.paths.image_dir
        )
        st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["current_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["db_flag"] = False
        st.session_state["db"] = ""
        for db in cfg.navigation.databases:
            st.session_state[db] = build_markdown_database(
                str(cfg.paths.world_dir / db)
            )

    st.session_state["dashboard_config_errors"] = utils.validate_dashboard_views()

    main()
