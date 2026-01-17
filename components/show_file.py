import streamlit as st
import re
from config import cfg
from components import utils


def __process_tags(text: str) -> str:
    """Hebt #Tags farbig hervor."""
    return re.sub(r"#\w+", lambda m: f":blue-background[{m.group(0)}] \n", text)


def __process_text_block(text: str) -> str:
    """Verarbeitet einen Textabschnitt: Links & Tags hervorheben."""
    text = __make_internal_links_clickable(text)
    text = __process_tags(text)
    return text


def __make_internal_links_clickable(text: str) -> str:
    """Ersetzt [[Link]] durch klickbare HTML-Links mit ?page=... Parametern."""

    def replace_link(match):
        link_text = match.group(1).strip()
        target_path = utils.find_file_path_in_tree(
            st.session_state["tree"], f"{link_text}.md"
        )
        if target_path:
            # Encode den Pfad in den Link
            return f'<a href="?page={target_path}">{link_text}</a>'
        else:
            return link_text

    return re.sub(r"\[\[([^\]]+)\]\]", replace_link, text)


def show_image(pos: st, image: str, full_width: bool = True):
    pos.image(st.session_state["images"][image], use_container_width=full_width)


def show_file(file_path: str, columns=None):
    """Zeigt eine Markdown-Datei in Streamlit an, mit Bildern, Links und Tags."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # ------------------------------
        # 1. Dokument an Bildern splitten: ![[image.png]]
        # ------------------------------
        pattern = r"!\[\[([^\]]+)\]\]"
        parts = re.split(pattern, content)

        i = 0
        if columns is None:
            columns = st.columns([3, 1])
        while i < len(parts):
            text_part = parts[i]
            if text_part.strip():
                columns[0].markdown(
                    __process_text_block(text_part), unsafe_allow_html=True
                )

            if i + 1 < len(parts):
                filename = parts[i + 1]
                filename = str(filename).split("|")[0]
                image_path = filename
                is_image = any([img_kind in filename for img_kind in cfg.IMAGE_TYPES])
                if not is_image:
                    md_path = utils.find_file_path_in_tree(
                        st.session_state["tree"], f"{filename}.md"
                    )
                else:
                    md_path = None
                # display images
                if is_image:
                    show_image(columns[1], image_path)
                # display inserted markdown files
                elif md_path and utils.has_permission(
                    md_path, st.session_state["user"]
                ):
                    columns[0].markdown("---")
                    show_file(md_path, columns=columns)
                # skip game master files
                elif utils.has_permission(md_path, st.session_state["user"]):
                    pass
                # error case
                else:
                    st.error(f"Datei nicht gefunden: {filename}")
            i += 2

    except FileNotFoundError:
        st.error(f"Datei nicht gefunden: `{file_path}`")
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei `{file_path}`: {e}")
