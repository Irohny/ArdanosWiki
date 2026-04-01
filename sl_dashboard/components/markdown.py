import re
import streamlit as st
from urllib.parse import urlencode

from components import utils


LINKED_WIKI_PAGE_QUERY_PARAM = "sl_linked_page"
ACTIVE_SCENE_QUERY_PARAM = "sl_scene"


def _normalize_query_param_value(value) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def _current_query_params() -> dict[str, str]:
    return {
        key: _normalize_query_param_value(value)
        for key, value in st.query_params.items()
    }


def set_query_param(name: str, value: str | None) -> None:
    if value:
        st.query_params[name] = value
        return
    if name in st.query_params:
        del st.query_params[name]


def build_linked_page_href(target_path: str) -> str:
    params = _current_query_params()
    params[LINKED_WIKI_PAGE_QUERY_PARAM] = target_path
    return f"?{urlencode(params)}"


def _make_internal_links_clickable(text: str) -> str:
    def replace_link(match):
        link_text = match.group(1).strip()
        target_path = utils.find_file_path_in_tree(
            st.session_state["tree"], f"{link_text}.md"
        )
        if not target_path:
            return link_text

        href = build_linked_page_href(target_path)
        return (
            f'<a href="{href}" '
            f'target="_self" rel="noopener noreferrer">{link_text}</a>'
        )

    return re.sub(r"\[\[([^\]]+)\]\]", replace_link, text)


def render_wiki_markdown(text: str) -> None:
    if not text:
        return
    st.markdown(_make_internal_links_clickable(text), unsafe_allow_html=True)


def wiki_markdown(text: str) -> str:
    if not text:
        return ""
    return _make_internal_links_clickable(text)
