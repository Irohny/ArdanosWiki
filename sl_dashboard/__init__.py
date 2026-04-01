from pathlib import Path

from sl_dashboard.components.shell import render_sl_dashboard_shell
from sl_dashboard.demo_data import build_demo_dashboard_data
from sl_dashboard.loader import load_dashboard_data


def render_sl_dashboard(session_dir: Path | None = None) -> None:
    try:
        dashboard_data = load_dashboard_data(session_dir=session_dir)
    except (FileNotFoundError, ValueError):
        dashboard_data = build_demo_dashboard_data()

    render_sl_dashboard_shell(dashboard_data)
