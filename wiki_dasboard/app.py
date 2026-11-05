from pathlib import Path
import sys
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


def open_dialog_page_as_main_page(file_path: str) -> None:
    utils.set_path(file_path)
    st.query_params.pop(WIKI_DIALOG_QUERY_PARAM, None)


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
        div[data-testid="stDialog"] button[aria-label="Close"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([5, 1])
    cols[0].subheader(Path(file_path).stem)
    if cols[1].button(
        "->",
        key="open_dialog_page_as_new_main_page",
        help="Als Hauptseite öffnen",
    ):
        open_dialog_page_as_main_page(file_path)
        st.rerun()
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
        role=Roles(expected_role),
        loged_in=True,
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
    # set session state if query parameter are give (click on document link)
    if "page" in st.query_params:
        st.session_state["current_path"] = st.query_params["page"]
    database_view = st.query_params.get(DATABASE_VIEW_QUERY_PARAM)
    if database_view in cfg.DATABASE_LIST:
        st.session_state["db"] = database_view
        st.session_state["db_flag"] = True
    elif database_view:
        st.query_params.pop(DATABASE_VIEW_QUERY_PARAM, None)
    header()
    create_sidebar()
    linked_page = st.query_params.get(WIKI_DIALOG_QUERY_PARAM)
    if linked_page:
        linked_page = str(linked_page)
        if linked_page in utils.get_all_file_paths(st.session_state["tree"]):
            render_wiki_dialog(linked_page)
        else:
            st.query_params.pop(WIKI_DIALOG_QUERY_PARAM, None)


if __name__ == "__main__":
    st.set_page_config(
        "DnD Wiki", page_icon=f"{cfg.IMAGE_DIR}/dnd_logo.svg", layout="wide"
    )
    user = ensure_app_user()
    if not user.loged_in:
        render_login_screen()
        st.stop()

    if "root_path" not in st.session_state:
        st.session_state["tree"] = utils.find_markdown_files(
            cfg.MARKDOWN_DIR, st.session_state["user"]
        )
        st.session_state["images"] = utils.collect_images_by_name(cfg.IMAGE_DIR)
        st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["current_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["db_flag"] = False
        st.session_state["db"] = ""
        for db in cfg.DATABASE_LIST:
            st.session_state[db] = build_markdown_database(
                str(cfg.MARKDOWN_DIR / db)
            )

    st.session_state["dashboard_config_errors"] = utils.validate_dashboard_views()

    main()
