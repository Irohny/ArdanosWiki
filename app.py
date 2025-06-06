import streamlit as st

from components.sidebar import create_sidebar
from components.header import header
from components import utils
from config import cfg
from components.login import User


def main():
    # set session state if query parameter are give (click on document link)
    if "page" in st.query_params:
        st.session_state["current_path"] = st.query_params["page"]
    header()
    create_sidebar()


if __name__ == "__main__":
    st.set_page_config(
        "DnD Wiki", page_icon=f"{cfg.IMAGE_DIR}/dnd_logo.svg", layout="wide"
    )
    if "root_path" not in st.session_state:
        st.session_state["user"] = User()
        st.session_state["tree"] = utils.find_markdown_files(
            cfg.MARKDOWN_DIR, st.session_state["user"]
        )
        st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["current_path"] = str(list(st.session_state["tree"].keys())[0])

    main()
