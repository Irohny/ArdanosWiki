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
    scene_number: int,
    total_scenes: int,
    phase_label: str,
) -> None:
    is_active = active_scene_title == scene.title
    status_label = scene.status.strip().capitalize() or "-"
    with st.container(border=True):
        content_col, action_col = st.columns((5, 1), gap="small")
        with content_col:
            st.caption(f"{phase_label} | Szene {scene_number} von {total_scenes}")
            if is_active:
                st.markdown(f"**{scene.title}**")
            else:
                st.markdown(scene.title)
            st.caption(f"Ort: {scene.location or '-'} | Status: {status_label}")
        with action_col:
            st.button(
                "->",
                key=f"scene-open::{scene.title}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                help="Szene aktivieren",
                on_click=_set_active_value,
                args=(state_key, scene.title),
            )


def render_scene_focus_card(
    scene: DashboardScene,
    *,
    state_key: str,
    previous_scene_title: str | None,
    next_scene_title: str | None,
    active_scene_number: int,
    total_scenes: int,
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
        st.caption(f"Aktuelle Szene {active_scene_number} von {total_scenes}")

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

    if scene.goal:
        with st.expander("Szenenziel", expanded=False):
            render_wiki_markdown(scene.goal)

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

    active_index = next(
        (
            index
            for index, scene in enumerate(ordered_scenes)
            if scene.title == active_scene_title
        ),
        0,
    )
    total_scenes = len(ordered_scenes)
    completed_scenes = ordered_scenes[:active_index]
    active_scene = ordered_scenes[active_index]
    upcoming_scenes = ordered_scenes[active_index + 1 :]

    if completed_scenes:
        for scene_number, scene in enumerate(completed_scenes, start=1):
            _render_scene_summary(
                scene,
                active_scene_title,
                state_key=state_key,
                scene_number=scene_number,
                total_scenes=total_scenes,
                phase_label="Vorher",
            )

    _render_scene_summary(
        active_scene,
        active_scene_title,
        state_key=state_key,
        scene_number=active_index + 1,
        total_scenes=total_scenes,
        phase_label="Aktiv",
    )

    if not upcoming_scenes:
        return

    for offset, scene in enumerate(upcoming_scenes, start=1):
        _render_scene_summary(
            scene,
            active_scene_title,
            state_key=state_key,
            scene_number=active_index + offset + 1,
            total_scenes=total_scenes,
            phase_label="Als naechstes" if offset == 1 else "Spaeter",
        )
