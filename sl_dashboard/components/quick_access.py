from urllib.parse import urlencode

import streamlit as st

from config import cfg
from sl_dashboard.models import DashboardLink, DashboardNpc


def _build_wiki_page_href(target_path: str) -> str:
    return f"{cfg.WIKI_APP_BASE_URL}/?{urlencode({'page': target_path})}"


def _render_link_card(
    title: str,
    *,
    caption: str | None = None,
    button_key: str,
    wiki_target: str | None,
    is_active: bool,
) -> None:
    with st.container(border=True):
        header_col, action_col = st.columns((3, 1), vertical_alignment="top")
        header_col.markdown(f"**{title}**")
        with action_col:
            if wiki_target:
                st.link_button(
                    "->",
                    url=_build_wiki_page_href(wiki_target),
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                )
            else:
                st.button(
                    "-",
                    key=button_key,
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    disabled=True,
                )
        if caption:
            st.caption(caption)


def render_quick_links(
    links: tuple[DashboardLink, ...],
    *,
    allowed_contexts: tuple[str, ...] | None = None,
    active_title: str | None = None,
) -> None:
    filtered_links = links
    if allowed_contexts is not None:
        normalized_contexts = {context.casefold() for context in allowed_contexts}
        filtered_links = tuple(
            link for link in links if link.context.casefold() in normalized_contexts
        )

    if not filtered_links:
        st.caption("Keine passenden Schnellzugriffe vorhanden.")
        return

    for link in filtered_links:
        _render_link_card(
            link.title,
            button_key=f"detail-link::{link.context}::{link.title}",
            wiki_target=link.source_file or None,
            is_active=active_title == link.title,
        )


def render_active_npcs(
    npcs: tuple[DashboardNpc, ...],
    *,
    active_name: str | None = None,
) -> None:
    if not npcs:
        st.caption("Noch keine NSCs markiert.")
        return

    for npc in npcs:
        caption_parts = [value for value in (npc.species, npc.title) if value]
        _render_link_card(
            npc.name,
            caption=" | ".join(caption_parts) if caption_parts else None,
            button_key=f"detail-npc::{npc.name}",
            wiki_target=npc.source_file or None,
            is_active=active_name == npc.name,
        )
