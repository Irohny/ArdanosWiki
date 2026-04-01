import streamlit as st

from sl_dashboard.components.markdown import (
    ACTIVE_SCENE_QUERY_PARAM,
    render_wiki_markdown,
    set_query_param,
)
from sl_dashboard.models import DashboardScene


def _set_active_value(state_key: str, state_value: str) -> None:
    st.session_state[state_key] = state_value
    set_query_param(ACTIVE_SCENE_QUERY_PARAM, state_value)


def _render_text_block(text: str) -> None:
    if not text:
        return
    render_wiki_markdown(text)


def _render_section(title: str, items: tuple[str, ...]) -> None:
    if not items:
        return

    st.markdown(f"**{title}**")
    if len(items) == 1 and "\n" in items[0]:
        render_wiki_markdown(items[0])
        return

    for item in items:
        render_wiki_markdown(f"- {item}")


def _render_scene_summary(
    scene: DashboardScene,
    active_scene_title: str,
    *,
    state_key: str,
) -> None:
    is_active = active_scene_title == scene.title
    title_color = "#63391f" if is_active else "#352619"

    with st.container(border=True):
        header_col, action_col = st.columns((4, 1), vertical_alignment="top")
        header_col.markdown(
            f'<div style="font-weight: 700; color: {title_color}; padding-top: 0.35rem;">{scene.title}</div>',
            unsafe_allow_html=True,
        )
        action_col.button(
            "->",
            key=f"scene-open::{scene.title}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            on_click=_set_active_value,
            args=(state_key, scene.title),
        )


def render_scene_focus_card(
    scene: DashboardScene,
    *,
    state_key: str,
    previous_scene_title: str | None,
    next_scene_title: str | None,
) -> None:
    prev_col, title_col, next_col = st.columns((1, 6, 1), vertical_alignment="center")

    with prev_col:
        st.button(
            "<-",
            key=f"scene-nav-prev::{scene.title}",
            use_container_width=True,
            type="secondary",
            disabled=previous_scene_title is None,
            on_click=_set_active_value,
            args=(
                (state_key, previous_scene_title)
                if previous_scene_title is not None
                else (state_key, scene.title)
            ),
        )

    with title_col:
        st.subheader(scene.title)

    with next_col:
        st.button(
            "->",
            key=f"scene-nav-next::{scene.title}",
            use_container_width=True,
            type="secondary",
            disabled=next_scene_title is None,
            on_click=_set_active_value,
            args=(
                (state_key, next_scene_title)
                if next_scene_title is not None
                else (state_key, scene.title)
            ),
        )

    with st.expander("Szenenbeschreibung", expanded=True):
        render_wiki_markdown(scene.summary)

    con2 = st.container(border=True)
    con2.markdown("**Szenennotizen**")
    if scene.discoveries:
        with con2:
            _render_section("Was es zu entdecken gibt", scene.discoveries)

    if scene.stakes:
        with con2:
            _render_section("Was auf dem Spiel steht", scene.stakes)

    if scene.pressure:
        con2.markdown("**Druck**")
        with con2:
            render_wiki_markdown(scene.pressure)

    if scene.likely_player_actions:
        with con2:
            _render_section(
                "Wahrscheinliche Spieleraktionen",
                scene.likely_player_actions,
            )

    if scene.hidden_truths:
        with con2:
            _render_section(
                "Verdeckte Wahrheiten fuer die SL",
                scene.hidden_truths,
            )


def render_next_scenes(
    ordered_scenes: tuple[DashboardScene, ...],
    active_scene_title: str,
    *,
    state_key: str,
) -> None:
    if not ordered_scenes:
        st.caption("Noch keine Folgeszenen definiert.")
        return

    active_scene = ordered_scenes[0]
    _render_scene_summary(active_scene, active_scene_title, state_key=state_key)

    next_scene = ordered_scenes[1] if len(ordered_scenes) > 1 else None
    if next_scene is not None:
        _render_scene_summary(next_scene, active_scene_title, state_key=state_key)

    remaining_scenes = ordered_scenes[2:]
    if not remaining_scenes:
        return

    st.markdown("---")
    for scene in remaining_scenes:
        _render_scene_summary(scene, active_scene_title, state_key=state_key)
