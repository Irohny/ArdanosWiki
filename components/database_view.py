import streamlit as st
from components import utils
import pandas as pd


def show_database(db: str):
    if "Bestiarium" in db:
        bestiarium_view()
    elif "Zauberarchiv" in db:
        zauberarchiev_view()
    elif "Tranksammlung" in db:
        trank_view()
    elif "Zutatenarchiv" in db:
        zutaten_view()


def set_to_databse_view(db: str):
    st.session_state["db_flag"] = True
    st.session_state["db"] = db


def show_table(df: pd.DataFrame, columns: list[str]):
    cols = st.columns(len(columns))
    for i, c in enumerate(columns):
        if c == "Pfad":
            cols[i].subheader("Infos")
            continue
        cols[i].subheader(c)
    st.markdown("---")
    for _, row in df.iterrows():
        cols = st.columns(len(columns))
        for i, c in enumerate(columns):
            if c == "Pfad":
                cols[i].button(
                    "Mehr",
                    key=f"{row['Name']}_view",
                    use_container_width=True,
                    type="tertiary",
                    on_click=utils.set_path,
                    args=(row[c],),
                )
                continue
            cols[i].markdown(row[c])
        st.markdown("---")


def bestiarium_view():
    columns = [
        "Name",
        "Stufe",
        "Volk",
        "Gesinnung",
        "Rüstungsklasse",
        "Grundlage",
        "Pfad",
    ]
    show_table(st.session_state["Bestiarium"], columns)


def zauberarchiev_view():
    columns = [
        "Name",
        "Grad",
        "Schule",
        "Komponenten",
        "Konzentration",
        "Pfad",
    ]
    show_table(st.session_state["Zauberarchiv"], columns)


def trank_view():
    columns = [
        "Name",
        "Tags",
        "Wert",
        "Seltenheit",
        "Pfad",
    ]
    show_table(st.session_state["Tranksammlung"], columns)


def zutaten_view():
    columns = [
        "Name",
        "Wert",
        "Seltenheit",
        "Fundort",
        "Pfad",
    ]
    show_table(st.session_state["Zutatenarchiv"], columns)
