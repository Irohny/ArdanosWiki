import streamlit as st

from wiki_dasboard.components.encounter_calculator import encounter_calculator_view
from wiki_dasboard.components.entry_creator import ENTRY_CONFIGS, entry_creator_view
from wiki_dasboard.components.monster_creator import render_monster_creator_view
from wiki_dasboard.components.npc_creator import npc_creator_view
from wiki_dasboard.components import utils
from wiki_dasboard.config import cfg


TOOLBOX_TOOL_STATE_KEY = "toolbox_selected_tool"
TOOLBOX_TOOLS = (
    "Encounter Rechner",
    "NSC Ersteller",
    "Monster Ersteller",
    *ENTRY_CONFIGS.keys(),
)


def set_to_toolbox_view() -> None:
    st.session_state["db_flag"] = True
    st.session_state["db"] = cfg.TOOLBOX_FEATURE_NAME
    st.query_params.pop(utils.DATABASE_VIEW_QUERY_PARAM, None)
    st.query_params.pop(utils.WIKI_DIALOG_QUERY_PARAM, None)


def toolbox_view(*, show_title: bool = True) -> None:
    set_to_toolbox_view()
    if show_title:
        st.subheader(cfg.TOOLBOX_FEATURE_NAME)
    selected_tool = st.pills(
        "Werkzeug",
        TOOLBOX_TOOLS,
        key=TOOLBOX_TOOL_STATE_KEY,
        default=TOOLBOX_TOOLS[0],
        label_visibility="collapsed"
    )

    if selected_tool == "Encounter Rechner":
        encounter_calculator_view()
    elif selected_tool == "NSC Ersteller":
        npc_creator_view()
    elif selected_tool == "Monster Ersteller":
        render_monster_creator_view()
    elif selected_tool in ENTRY_CONFIGS:
        entry_creator_view(selected_tool)

    set_to_toolbox_view()