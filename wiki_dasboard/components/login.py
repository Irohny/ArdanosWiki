import streamlit as st
from enum import Enum
from collections.abc import Iterable
from wiki_dasboard.components.auth import (
    clear_auth_cookie,
    lookup_user_record,
    persist_auth_claims,
)
from wiki_dasboard.components import utils
from wiki_dasboard.config import cfg


class Roles(Enum):
    Default = "Default"
    Player = "Player"
    GameMaster = "GameMaster"


class User:
    def __init__(
        self,
        name: str | None = None,
        password: str | None = None,
        role: Roles = Roles.Default,
        loged_in: bool = False,
        character_ids: Iterable[str] | None = None,
        user_name: str | None = None,
        campaigns: Iterable[object] | None = None,
    ):
        self.name: str = name
        self.user_name: str = user_name or name
        self.password: str = password
        self.role: Roles = role
        self.loged_in: bool = loged_in
        if character_ids is None:
            self.character_ids = None
        elif isinstance(character_ids, str):
            self.character_ids = (character_ids,)
        else:
            self.character_ids = tuple(character_ids)
        self.campaigns = tuple(campaigns or ())


def login_filed(place):
    if st.session_state.pop("auth_cookie_clear_pending", False):
        clear_auth_cookie()

    if st.session_state["user"].loged_in:
        place.markdown(
            f"Hallo **{st.session_state['user'].name}**, viel Spaß in Andaros."
        )
        place.button("Logout", on_click=logout)
    else:
        form = place.form("login_filed")
        form.text_input("Benutzername:", key="user_name")
        form.text_input("Passwort", key="password", type="password")
        form.form_submit_button("Login", on_click=check_login_data)


def check_login_data():
    user_name = str(st.session_state.get("user_name", "")).strip()
    user = lookup_user_record(user_name)
    if user is None or st.session_state.get("password") != user.get("password"):
        return

    try:
        role = Roles(str(user.get("role", Roles.Default.value)))
    except ValueError:
        return

    login_name = str(user.get("user_name", user_name)).strip()
    st.session_state["user"] = User(
        name=str(user.get("name", login_name)),
        user_name=login_name,
        password=str(user.get("password", "")),
        role=role,
        loged_in=True,
        character_ids=user.get("characters", user.get("charakter")),
        campaigns=user.get("campaigns"),
    )
    st.session_state["tree"] = utils.find_markdown_files(
        cfg.paths.world_dir, st.session_state["user"]
    )
    persist_auth_claims(login_name, role.value)


def logout():
    st.session_state["auth_cookie_clear_pending"] = True
    st.session_state["user"] = User()
    for key in (
        "active_campaign_id",
        "wiki_campaign_selector",
        "campaign_overview_mode",
        "campaign_overview_expanded_folders",
        "ardanos_map_open",
        "ardanos_map_marker_types",
        "root_path",
        "current_path",
    ):
        st.session_state.pop(key, None)
    st.session_state["tree"] = utils.find_markdown_files(
        cfg.paths.world_dir, st.session_state["user"]
    )
