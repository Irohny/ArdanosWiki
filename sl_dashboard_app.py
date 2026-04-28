import streamlit as st
from sl_dashboard.app_runtime import prepare_dashboard_navigation, resolve_page_title


def main() -> None:
    current_page = prepare_dashboard_navigation()
    if current_page is None:
        return
    current_page.run()


if __name__ == "__main__":
    st.set_page_config(
        page_title=resolve_page_title(),
        page_icon="🎲",
        layout="wide",
    )
    main()
