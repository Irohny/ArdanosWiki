import streamlit as st
from enum import Enum


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
    ):
        self.name: str = name
        self.password: str = password
        self.role: Roles = role
        self.loged_in: bool = loged_in


def login_filed(place: st):
    if st.session_state["user"].loged_in:
        place.markdown(
            f"Hallo **{st.session_state['user'].name}**, viel Spaß in Andaros."
        )
        place.button("Logout", on_click=logout)
    else:
        form = place.form("login_filed")
        form.text_input("Charaktername:", key="charackter_name")
        form.text_input("Passwort", key="password")
        form.form_submit_button("Login", on_click=check_login_data)


def check_login_data():
    for user in st.secrets["users"]:
        if (
            st.session_state["charackter_name"] == user["name"]
            and st.session_state["password"] == user["password"]
        ):
            st.session_state["user"] = User(
                name=user["name"],
                password=user["password"],
                role=Roles(user["role"]),
                loged_in=True,
            )
            return


def logout():
    st.session_state["user"] = User()
