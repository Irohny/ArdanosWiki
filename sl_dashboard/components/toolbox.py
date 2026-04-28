import streamlit as st

from sl_dashboard.components.markdown import render_wiki_markdown
from sl_dashboard.models import DashboardTool


def render_notes(notes: tuple[str, ...]) -> None:
    if len(notes) == 1 and "\n" in notes[0]:
        render_wiki_markdown(notes[0])
        return

    for note in notes:
        render_wiki_markdown(f"- {note}")


def render_toolbox(tools: tuple[DashboardTool, ...], notes: tuple[str, ...]) -> None:
    if not tools:
        st.caption("Noch keine Werkzeuge eingebunden.")
    for tool in tools:
        with st.container(border=True):
            st.markdown(f"**{tool.title}**")
            label = tool.status
            if tool.emphasis == "hoch":
                label = f"prioritaet | {tool.status}"
            st.caption(label)
            st.write(tool.description)

    if not notes:
        st.caption("Noch keine Sitzungsnotizen vorhanden.")
        return

    render_notes(notes)
