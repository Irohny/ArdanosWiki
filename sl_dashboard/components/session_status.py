import streamlit as st

from sl_dashboard.components.markdown import render_wiki_markdown
from sl_dashboard.models import SessionStatus


def _render_status_list(items: tuple[str, ...]) -> None:
    if len(items) == 1 and "\n" in items[0]:
        render_wiki_markdown(items[0])
        return

    for item in items:
        render_wiki_markdown(f"- {item}")


def render_session_status_card(status: SessionStatus) -> None:
    if status.current_goal:
        st.markdown("**Sitzungsziel**")
        render_wiki_markdown(status.current_goal)

    if status.pacing:
        st.markdown(f"**Pacing:** {status.pacing}")

    st.markdown("**Offene Faeden**")
    if not status.open_threads:
        st.caption("Noch keine offenen Faeden notiert.")
        return

    _render_status_list(status.open_threads)
