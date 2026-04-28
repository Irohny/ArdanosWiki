from urllib.parse import urlencode

import streamlit as st

from config import cfg
from sl_dashboard.models import DashboardLink, DashboardNpc


def _build_wiki_page_href(target_path: str) -> str:
    return f"{cfg.WIKI_APP_BASE_URL}/?{urlencode({'page': target_path})}"


def _render_link_row(
    title: str,
    *,
    details: str | None = None,
    button_key: str,
    wiki_target: str | None,
) -> None:
    name_col, meta_col, action_col = st.columns((3.6, 2.4, 1.0), gap="small")
    name_col.markdown(f"**{title}**")
    meta_col.caption(details or "-")

    if wiki_target:
        action_col.link_button(
            "->",
            url=_build_wiki_page_href(wiki_target),
            use_container_width=True,
            type="secondary",
        )
    else:
        action_col.button(
            "->",
            key=f"{button_key}::missing-wiki",
            use_container_width=True,
            type="secondary",
            disabled=True,
        )

    st.divider()


def _build_npc_detail_lines(npc: DashboardNpc) -> tuple[str, str]:
    species_line = npc.species or "-"
    return species_line, npc.location or "-"


def _render_npc_row(npc: DashboardNpc) -> None:
    name_col, details_col, action_col = st.columns((2, 3, 1), gap="small")
    species_line, extra_line = _build_npc_detail_lines(npc)

    name_col.markdown(f"**{npc.name}**")
    details_col.caption(species_line)
    details_col.caption(extra_line)

    if npc.source_file:
        action_col.link_button(
            "->",
            url=_build_wiki_page_href(npc.source_file),
            use_container_width=True,
            type="secondary",
        )

    st.divider()


def render_quick_links(
    links: tuple[DashboardLink, ...],
    *,
    allowed_contexts: tuple[str, ...] | None = None,
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
        _render_link_row(
            link.title,
            details=link.reason or link.context,
            button_key=f"detail-link::{link.context}::{link.title}",
            wiki_target=link.source_file or None,
        )


def render_active_npcs(
    npcs: tuple[DashboardNpc, ...],
) -> None:
    if not npcs:
        st.caption("Noch keine NSCs markiert.")
        return

    for npc in npcs:
        _render_npc_row(npc)
