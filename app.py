import streamlit as st

from components.sidebar import create_sidebar
from components import utils
from config import cfg


def main():
    if not st.session_state["current_path"].endswith(".md"):
        st.title("D&D Kampagnen-Wiki")
    create_sidebar()
    print(st.session_state["current_path"])


if __name__ == "__main__":
    st.session_state["tree"] = utils.find_markdown_files(cfg.MARKDOWN_DIR)
    if "root_path" not in st.session_state:
        st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["current_path"] = str(list(st.session_state["tree"].keys())[0])

    main()
