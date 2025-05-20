import streamlit as st

from components.sidebar import create_sidebar
from components import utils
from config import cfg


def main():
    # set session state if query parameter are give (click on document link)
    if "page" in st.query_params:
        st.session_state["current_path"] = st.query_params["page"]

    if not st.session_state["current_path"].endswith(".md"):
        st.markdown(f":gray-badge[{st.session_state['current_path']}]")
        col = st.columns([1, 15])
        col[0].image(f"{cfg.IMAGE_DIR}/dnd_logo.svg", use_container_width=True)
        col[1].title(":red[Ardanos Wiki]")
        st.header(f"{st.session_state['current_path'].split('/')[-1]}")
        st.text(
            """Navigiere mit der Sidebar durch das Wiki und erkunde die Ecken von Andaros. Mit zurück kommst du in den vorherigen Ordner. Viel Spaß und melde dich, wenn du mal wieder eine Runde in diesem Universum spielen willst."""
        )
        st.image(f"{cfg.IMAGE_DIR}/Ardanos.jpeg")
    create_sidebar()


if __name__ == "__main__":
    st.set_page_config(
        "DnD Wiki", page_icon=f"{cfg.IMAGE_DIR}/dnd_logo.svg", layout="wide"
    )
    st.session_state["tree"] = utils.find_markdown_files(cfg.MARKDOWN_DIR)
    if "root_path" not in st.session_state:
        st.session_state["root_path"] = str(list(st.session_state["tree"].keys())[0])
        st.session_state["current_path"] = str(list(st.session_state["tree"].keys())[0])

    main()
