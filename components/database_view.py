import streamlit as st
import pandas as pd
from components.show_file import make_internal_links_clickable
import re


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


def process_option(options: list[str]) -> list[str]:
    filtering = [False]
    for j, opt in enumerate(options):
        if isinstance(opt, str) and "#" in opt:
            filtering.append(True)
    if not any(filtering):
        return options
    alternatives = []
    for opt in options:
        alternatives.extend(opt.split("#")[1:])
    return alternatives


def show_table(
    df: pd.DataFrame,
    columns: list[str],
    column_filter: list[str] | None = None,
    db: str = "",
):
    if column_filter is not None:
        cols = st.columns(len(column_filter))
        for i, cf in enumerate(column_filter):
            options = list(df[cf].unique())
            options = process_option(options)
            cols[i].multiselect(
                cf,
                options,
                key=f"filter_{cf}",
                on_change=set_to_databse_view,
                args=(db,),
            )

    if column_filter is not None:
        for cf in column_filter:
            if len(st.session_state[f"filter_{cf}"]) > 0:
                pattern = "|".join(map(re.escape, st.session_state[f"filter_{cf}"]))
                df = df[df[cf].str.contains(pattern, case=False, na=False)]

    df.sort_values("Name", inplace=True, ignore_index=True)
    cols = st.columns(len(columns))
    for i, c in enumerate(columns):
        cols[i].subheader(c)
    st.markdown("---")
    for _, row in df.iterrows():
        cols = st.columns(len(columns))
        for i, c in enumerate(columns):
            text = row[c]
            if text is None:
                continue
            if c == "Name":
                text = make_internal_links_clickable(f"[[{text}]]")
            if "#" in text:
                text = ", ".join(text.split("#")[1:])
            cols[i].markdown(text, unsafe_allow_html=True)
        st.markdown("---")


def bestiarium_view():
    columns = [
        "Name",
        "Stufe",
        "Volk",
        "Gesinnung",
        "Rüstungsklasse",
        "Grundlage",
    ]
    show_table(st.session_state["Bestiarium"], columns, "Bestiarium")


def zauberarchiev_view():
    columns = [
        "Name",
        "Grad",
        "Schule",
        "Komponenten",
        "Konzentration",
    ]
    column_filter = ["Grad", "Schule", "Komponenten"]
    show_table(st.session_state["Zauberarchiv"], columns, column_filter, "Zauberarchiv")


def trank_view():
    columns = [
        "Name",
        "Tags",
        "Wert",
        "Seltenheit",
    ]
    column_filter = ["Seltenheit", "Tags"]
    show_table(
        st.session_state["Tranksammlung"], columns, column_filter, "Tranksammlung"
    )


def zutaten_view():
    columns = [
        "Name",
        "Wert",
        "Seltenheit",
        "Fundort",
    ]
    column_filter = ["Seltenheit"]
    show_table(
        st.session_state["Zutatenarchiv"], columns, column_filter
    ), "Zutatenarchiv"
