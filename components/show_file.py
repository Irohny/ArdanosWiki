import streamlit as st
import re
import os
from config import cfg


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


def show_file(file_path: str):
    """Zeigt eine Markdown-Datei in Streamlit an, mit Bildern, Links und Tags."""
    try:
        st.markdown(f":gray-badge[{file_path}]")
        title = os.path.basename(file_path).replace(".md", "")
        st.title(title)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            st.session_state["current_path"] = file_path

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
                image_filename = parts[i + 1]
                image_path = os.path.join(cfg.IMAGE_DIR, image_filename)
                if os.path.exists(image_path):
                    col = st.columns([1, 2])
                    col[0].image(image_path)
                else:
                    st.error(f"Bild nicht gefunden: {image_filename}")
            i += 2

    except FileNotFoundError:
        st.error(f"Datei nicht gefunden: `{file_path}`")
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei `{file_path}`: {e}")
