import streamlit as st
import re
import os
from config import cfg
from components import utils


def __process_links(text: str) -> str:
    """Hebt [[Links]] farbig hervor."""
    return re.sub(r"\[\[([^\]]+)\]\]", r":blue[\1]", text)


def __process_tags(text: str) -> str:
    """Hebt #Tags farbig hervor."""
    return re.sub(r"#\w+", lambda m: f":blue-background[{m.group(0)}]", text)


def __process_text_block(text: str) -> str:
    """Verarbeitet einen Textabschnitt: Links & Tags hervorheben."""
    text = __process_links(text)
    text = __process_tags(text)
    return text


def show_file(file_path: str, with_title=True):
    """Zeigt eine Markdown-Datei in Streamlit an, mit Bildern, Links und Tags."""
    try:
        if with_title:
            st.markdown(f":gray-badge[{file_path}]")
            title = os.path.basename(file_path).replace(".md", "")
            st.title(title)
            st.session_state["current_path"] = file_path
        else:
            title = os.path.basename(file_path).replace(".md", "")
            st.header(title)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # ------------------------------
        # 1. Dokument an Bildern splitten: ![[image.png]]
        # ------------------------------
        pattern = r"!\[\[([^\]]+)\]\]"
        parts = re.split(pattern, content)

        # ------------------------------
        # 2. Ausgabe: Text → Bild → Text ...
        # ------------------------------
        i = 0
        while i < len(parts):
            text_part = parts[i]
            if text_part.strip():
                st.markdown(__process_text_block(text_part), unsafe_allow_html=True)

            if i + 1 < len(parts):
                filename = parts[i + 1]
                filename = str(filename).split("|")[0]
                image_path = os.path.join(cfg.IMAGE_DIR, filename)
                is_image = any([img_kind in filename for img_kind in cfg.IMAGE_TYPES])
                if not is_image:
                    md_path = utils.find_file_path_in_tree(
                        st.session_state["tree"], f"{filename}.md"
                    )
                else:
                    md_path = None
                print(filename, md_path)
                # skip game master files
                if filename.startswith("sl "):
                    pass
                # display images
                elif is_image:
                    col = st.columns([1, 2])
                    col[0].image(image_path)
                # display inserted markdown files
                elif md_path:
                    show_file(md_path, with_title=False)
                # error case
                else:
                    st.error(f"Datei nicht gefunden: {filename}")
            i += 2

    except FileNotFoundError:
        st.error(f"Datei nicht gefunden: `{file_path}`")
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei `{file_path}`: {e}")
