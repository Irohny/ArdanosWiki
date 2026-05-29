import streamlit as st

from components.auth import clear_auth_cookie, load_auth_claims_from_cookie, lookup_user_record
from components.sidebar import create_sidebar
from components.header import header
from components import utils
from config import cfg
from components.login import Roles, User, login_filed
from components.file_parser import build_markdown_database


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
    header()
    create_sidebar()


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
            st.session_state[db] = build_markdown_database(f"World/{db}")

    st.session_state["dashboard_config_errors"] = utils.validate_dashboard_views()

    main()
