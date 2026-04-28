import streamlit as st

from sl_dashboard.components.markdown import render_wiki_markdown
from sl_dashboard.models import SessionStatus


def _render_status_list(items: tuple[str, ...]) -> None:
    if len(items) == 1 and "\n" in items[0]:
        render_wiki_markdown(items[0])
        return

    for item in items:
        render_wiki_markdown(f"- {item}")


def has_session_status_content(
    status: SessionStatus,
    *,
    alerts: tuple[str, ...] = (),
) -> bool:
    return bool(status.current_goal or alerts)


def render_session_status_card(
    status: SessionStatus,
    *,
    alerts: tuple[str, ...] = (),
) -> None:
    if status.current_goal:
        st.markdown("**Sitzungsziel**")
        render_wiki_markdown(status.current_goal)

    if alerts:
        st.markdown("**Warnungen**")
        _render_status_list(alerts)
