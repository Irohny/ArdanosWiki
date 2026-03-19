import streamlit as st

from config import DashboardViewConfig, cfg
from components.show_file import show_image
from components import utils


DEFAULT_DASHBOARD_TEXT = (
    "Navigiere mit der Sidebar durch das Wiki und erkunde die Ecken von Andaros. "
    "Mit zurück kommst du in den vorherigen Ordner. Viel Spaß und melde dich, "
    "wenn du mal wieder eine Runde in diesem Universum spielen willst."
)


def render_default_dashboard() -> None:
    st.text(DEFAULT_DASHBOARD_TEXT)
    cols = st.columns([1, 7])
    for emblem in cfg.DEFAULT_DASHBOARD_EMBLEMS:
        show_image(cols[0], emblem)
    show_image(cols[1], cfg.DEFAULT_DASHBOARD_BACKGROUND)


def render_vertical_spacing(spacing_rem: float) -> None:
    if spacing_rem <= 0:
        return
    st.markdown(
        f'<div style="height: {spacing_rem}rem;"></div>',
        unsafe_allow_html=True,
    )


def render_timeline_dashboard(view: DashboardViewConfig) -> None:
    if view.asset_path is None:
        render_default_dashboard()
        return

    timeline_path = utils.resolve_dashboard_asset_path(view)
    if timeline_path is None:
        st.info(
            f"Timeline nicht gefunden: {view.asset_path}. Fallback auf Standardansicht."
        )
        render_default_dashboard()
        return

    render_vertical_spacing(view.top_spacing_rem)
    target = st
    if view.layout_columns is not None:
        columns = st.columns(view.layout_columns)
        target = columns[1]

    target.image(str(timeline_path), use_container_width=view.use_container_width)
    if view.caption:
        target.caption(view.caption)


def render_dashboard(view: DashboardViewConfig | None) -> None:
    if view is None or view.mode == "default":
        render_default_dashboard()
        return

    if view.mode == "timeline":
        render_timeline_dashboard(view)
        return

    render_default_dashboard()
