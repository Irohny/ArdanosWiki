from pathlib import Path

from sl_dashboard.components.shell import (
    render_sl_dashboard_encounter_page,
    render_sl_dashboard_shell,
)
from sl_dashboard.demo_data import build_demo_dashboard_data
from sl_dashboard.loader import load_dashboard_data


def _load_dashboard_for_render(
    session_dir: Path | None = None,
) -> tuple[object, Path | None]:
    try:
        return load_dashboard_data(session_dir=session_dir), session_dir
    except (FileNotFoundError, ValueError):
        return build_demo_dashboard_data(), None


def render_sl_dashboard(session_dir: Path | None = None) -> None:
    dashboard_data, _ = _load_dashboard_for_render(session_dir=session_dir)

    render_sl_dashboard_shell(dashboard_data)


def render_sl_dashboard_encounter(session_dir: Path | None = None) -> None:
    dashboard_data, resolved_session_dir = _load_dashboard_for_render(
        session_dir=session_dir
    )

    render_sl_dashboard_encounter_page(
        dashboard_data,
        session_dir=resolved_session_dir,
    )
