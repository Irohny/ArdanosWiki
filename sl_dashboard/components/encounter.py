from pathlib import Path
import re
import unicodedata

import streamlit as st

from sl_dashboard.editor import (
    read_encounter_state,
    update_encounter_combatant,
    update_encounter_state,
)
from sl_dashboard.models import DashboardLink, DashboardScene, EncounterCombatant


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "combatant"


def _format_number(value: int | None) -> str:
    if value is None:
        return "-"
    return str(value)


COMMON_STATUS_EFFECTS = (
    "Geblendet",
    "Bezaubert",
    "Furcht",
    "Festgesetzt",
    "Gelähmt",
    "Liegend",
    "Unsichtbar",
    "Vergiftet",
    "Verlangsamt",
)


def _is_player_combatant(combatant: EncounterCombatant) -> bool:
    return combatant.source_type == "player" or combatant.side == "player"


def _format_defense_values(values: tuple[str, ...]) -> str:
    return ", ".join(value for value in values if value.strip()) or "-"


def _order_combatants_by_initiative(
    combatants: tuple[EncounterCombatant, ...],
) -> tuple[EncounterCombatant, ...]:
    return tuple(
        sorted(
            combatants,
            key=lambda combatant: (
                combatant.initiative is None,
                -(combatant.initiative or 0),
            ),
        )
    )


def _set_combatant_conditions(
    session_dir: Path,
    scene_id: str,
    combatant_id: str,
    condition_names: tuple[str, ...],
) -> None:
    state, scenes, encounter = _read_scene_encounter_state(session_dir, scene_id)
    if encounter is None:
        return

    runtime = encounter.get("runtime")
    if not isinstance(runtime, dict):
        return
    combatants = runtime.get("combatants")
    if not isinstance(combatants, list):
        return

    normalized_condition_names = tuple(
        dict.fromkeys(name.strip() for name in condition_names if name.strip())
    )

    for combatant in combatants:
        if not isinstance(combatant, dict):
            continue
        if str(combatant.get("id", "")) != combatant_id:
            continue

        existing_conditions = combatant.get("conditions")
        if not isinstance(existing_conditions, list):
            existing_conditions = []
        existing_by_name = {
            str(condition.get("name", "")).strip(): condition
            for condition in existing_conditions
            if isinstance(condition, dict)
        }
        combatant["conditions"] = [
            existing_by_name.get(name, {"name": name})
            for name in normalized_condition_names
        ]
        scenes[scene_id] = encounter
        update_encounter_state(session_dir, state)
        return


def _render_combatant_card(
    combatant: EncounterCombatant,
    *,
    session_dir: Path | None,
    scene_id: str,
) -> None:
    with st.container(border=True):
        is_player_combatant = _is_player_combatant(combatant)
        header_col, initiative_col = st.columns((4, 1), gap="small")
        header_col.markdown(f"**{combatant.name or 'Unbenannter Combatant'}**")
        initiative_col.caption(f"Ini {_format_number(combatant.initiative)}")

        meta_parts = [part for part in (combatant.side, combatant.source_type) if part]
        if meta_parts:
            st.caption(" | ".join(meta_parts))

        hp_text = (
            "extern"
            if is_player_combatant
            else f"{_format_number(combatant.current_hp)}/{_format_number(combatant.max_hp)}"
        )
        rk_text = "extern" if is_player_combatant else _format_number(combatant.armor_class)
        st.markdown(
            f"**HP** {hp_text}  |  **RK** {rk_text}  |  **Ini** {_format_number(combatant.initiative)}"
        )

        if not is_player_combatant and any(
            (combatant.immunities, combatant.resistances, combatant.weaknesses)
        ):
            st.caption(
                " | ".join(
                    (
                        f"Imm: {_format_defense_values(combatant.immunities)}",
                        f"Res: {_format_defense_values(combatant.resistances)}",
                        f"Schw: {_format_defense_values(combatant.weaknesses)}",
                    )
                )
            )

        if combatant.conditions:
            st.caption(
                "Status: "
                + ", ".join(condition.name for condition in combatant.conditions if condition.name)
            )
        else:
            st.caption("Status: -")

        if combatant.notes:
            st.caption(combatant.notes)

        if session_dir is None:
            return

        with st.popover("Bearbeiten", use_container_width=True):
            selected_conditions = st.multiselect(
                "Status",
                options=COMMON_STATUS_EFFECTS,
                default=[
                    condition.name
                    for condition in combatant.conditions
                    if condition.name in COMMON_STATUS_EFFECTS
                ],
                key=f"encounter-conditions::{scene_id}::{combatant.id}",
            )

            if is_player_combatant:
                initiative_value = st.number_input(
                    "Initiative",
                    min_value=0,
                    value=max(combatant.initiative or 0, 0),
                    step=1,
                    key=f"encounter-initiative::{scene_id}::{combatant.id}",
                )
                if st.button(
                    "Ini speichern",
                    key=f"encounter-initiative-save::{scene_id}::{combatant.id}",
                    use_container_width=True,
                ):
                    update_encounter_combatant(
                        session_dir,
                        scene_id,
                        combatant.id,
                        name=combatant.name,
                        side=combatant.side,
                        max_hp=combatant.max_hp,
                        current_hp=combatant.current_hp,
                        initiative=int(initiative_value),
                        armor_class=combatant.armor_class,
                    )
                    st.rerun()
            else:
                hp_value = st.number_input(
                    "Aktuelle HP",
                    min_value=0,
                    value=max(combatant.current_hp or 0, 0),
                    step=1,
                    key=f"encounter-hp::{scene_id}::{combatant.id}",
                )
                if st.button(
                    "HP speichern",
                    key=f"encounter-hp-save::{scene_id}::{combatant.id}",
                    use_container_width=True,
                ):
                    _update_combatant_hp(
                        session_dir,
                        scene_id,
                        combatant.id,
                        int(hp_value),
                    )
                    st.rerun()

            if st.button(
                "Status speichern",
                key=f"encounter-status-save::{scene_id}::{combatant.id}",
                use_container_width=True,
            ):
                _set_combatant_conditions(
                    session_dir,
                    scene_id,
                    combatant.id,
                    tuple(selected_conditions),
                )
                st.rerun()


def _read_scene_encounter_state(
    session_dir: Path,
    scene_id: str,
) -> tuple[dict, dict, dict | None]:
    state = read_encounter_state(session_dir)
    scenes = state.get("scenes")
    if not isinstance(scenes, dict):
        scenes = {}
    state["scenes"] = scenes
    encounter = scenes.get(scene_id)
    if encounter is not None and not isinstance(encounter, dict):
        encounter = None
    return state, scenes, encounter


def _write_scene_encounter_state(
    session_dir: Path,
    scene_id: str,
    encounter_record: dict | None,
) -> None:
    state, scenes, _ = _read_scene_encounter_state(session_dir, scene_id)
    if encounter_record is None:
        scenes.pop(scene_id, None)
    else:
        scenes[scene_id] = encounter_record
    update_encounter_state(session_dir, state)


def _default_encounter_state(monster_links: tuple[DashboardLink, ...]) -> dict:
    return {
        "status": "draft",
        "preparation": {
            "monster_source_keys": [link.title for link in monster_links],
        },
        "runtime": {
            "round_number": 1,
            "active_combatant_id": "",
            "combatants": [],
        },
        "notes": [],
    }


def _update_round(session_dir: Path, scene_id: str, delta: int) -> None:
    state, scenes, encounter = _read_scene_encounter_state(session_dir, scene_id)
    encounter = encounter or _default_encounter_state(())
    runtime = encounter.setdefault("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
        encounter["runtime"] = runtime
    current_round = runtime.get("round_number", 1)
    if not isinstance(current_round, int):
        current_round = 1
    runtime["round_number"] = max(1, current_round + delta)
    scenes[scene_id] = encounter
    update_encounter_state(session_dir, state)


def _add_combatant(
    session_dir: Path,
    scene_id: str,
    monster_links: tuple[DashboardLink, ...],
    *,
    name: str,
    side: str,
    max_hp: int,
    initiative: int,
    armor_class: int,
) -> None:
    state, scenes, encounter = _read_scene_encounter_state(session_dir, scene_id)
    encounter = encounter or _default_encounter_state(monster_links)
    runtime = encounter.setdefault("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
        encounter["runtime"] = runtime

    combatants = runtime.get("combatants")
    if not isinstance(combatants, list):
        combatants = []
        runtime["combatants"] = combatants

    base_id = _slugify(name)
    combatant_id = base_id
    existing_ids = {
        str(combatant.get("id", ""))
        for combatant in combatants
        if isinstance(combatant, dict)
    }
    suffix = 2
    while combatant_id in existing_ids:
        combatant_id = f"{base_id}-{suffix}"
        suffix += 1

    combatants.append(
        {
            "id": combatant_id,
            "name": name.strip(),
            "side": side,
            "max_hp": int(max_hp),
            "current_hp": int(max_hp),
            "initiative": int(initiative),
            "armor_class": int(armor_class),
            "conditions": [],
        }
    )
    runtime.setdefault("active_combatant_id", combatant_id)
    if not runtime.get("active_combatant_id"):
        runtime["active_combatant_id"] = combatant_id
    scenes[scene_id] = encounter
    update_encounter_state(session_dir, state)


def _update_combatant_hp(
    session_dir: Path,
    scene_id: str,
    combatant_id: str,
    current_hp: int,
) -> None:
    state, scenes, encounter = _read_scene_encounter_state(session_dir, scene_id)
    if encounter is None:
        return
    runtime = encounter.get("runtime")
    if not isinstance(runtime, dict):
        return
    combatants = runtime.get("combatants")
    if not isinstance(combatants, list):
        return

    for combatant in combatants:
        if not isinstance(combatant, dict):
            continue
        if str(combatant.get("id", "")) == combatant_id:
            combatant["current_hp"] = int(current_hp)
            scenes[scene_id] = encounter
            update_encounter_state(session_dir, state)
            return


def _add_condition(
    session_dir: Path,
    scene_id: str,
    combatant_id: str,
    *,
    name: str,
    duration: str,
) -> None:
    state, scenes, encounter = _read_scene_encounter_state(session_dir, scene_id)
    if encounter is None:
        return
    runtime = encounter.get("runtime")
    if not isinstance(runtime, dict):
        return
    combatants = runtime.get("combatants")
    if not isinstance(combatants, list):
        return

    for combatant in combatants:
        if not isinstance(combatant, dict):
            continue
        if str(combatant.get("id", "")) != combatant_id:
            continue

        conditions = combatant.get("conditions")
        if not isinstance(conditions, list):
            conditions = []
            combatant["conditions"] = conditions
        conditions.append(
            {
                "name": name.strip(),
                "duration": duration.strip(),
            }
        )
        scenes[scene_id] = encounter
        update_encounter_state(session_dir, state)
        return


def render_encounter_panel(
    active_scene: DashboardScene,
    monster_links: tuple[DashboardLink, ...],
    *,
    session_dir: Path | None,
) -> None:
    encounter = active_scene.encounter

    if encounter is None:
        with st.container(border=True):
            st.caption("Noch kein Encounter fuer diese Szene gespeichert.")
            if session_dir is None:
                st.caption("Im Demo-Modus kann kein Encounter gespeichert werden.")
            elif st.button(
                "Encounter anlegen",
                key=f"encounter-create::{active_scene.id}",
                use_container_width=True,
            ):
                _write_scene_encounter_state(
                    session_dir,
                    active_scene.id,
                    _default_encounter_state(monster_links),
                )
                st.rerun()
        return

    ordered_combatants = _order_combatants_by_initiative(
        encounter.runtime.combatants
    )

    with st.container(border=True):
        round_col = st.columns(1, gap="small")[0]
        round_col.markdown("**Runde**")
        round_col.caption(str(encounter.runtime.round_number))

        if session_dir is not None:
            prev_round_col, next_round_col = st.columns(2, gap="small")
            if prev_round_col.button(
                "Runde -1",
                key=f"encounter-round-minus::{active_scene.id}",
                use_container_width=True,
            ):
                _update_round(session_dir, active_scene.id, -1)
                st.rerun()
            if next_round_col.button(
                "Runde +1",
                key=f"encounter-round-plus::{active_scene.id}",
                use_container_width=True,
            ):
                _update_round(session_dir, active_scene.id, 1)
                st.rerun()

        if not ordered_combatants:
            st.caption("Noch keine Combatants im Encounter hinterlegt.")
        else:
            for start_index in range(0, len(ordered_combatants), 3):
                row_columns = st.columns(3, gap="small")
                for column, combatant in zip(
                    row_columns,
                    ordered_combatants[start_index : start_index + 3],
                ):
                    with column:
                        _render_combatant_card(
                            combatant,
                            session_dir=session_dir,
                            scene_id=active_scene.id,
                        )

        if encounter.notes:
            st.markdown("**Notizen**")
            for note in encounter.notes:
                st.write(f"- {note}")

        if session_dir is not None:
            with st.expander("Combatant hinzufuegen"):
                with st.form(key=f"encounter-add-combatant::{active_scene.id}"):
                    name = st.text_input("Name", key=f"encounter-add-name::{active_scene.id}")
                    side = st.selectbox(
                        "Seite",
                        options=("enemy", "ally", "player", "npc"),
                        key=f"encounter-add-side::{active_scene.id}",
                    )
                    max_hp = st.number_input(
                        "Max HP",
                        min_value=1,
                        value=10,
                        step=1,
                        key=f"encounter-add-maxhp::{active_scene.id}",
                    )
                    initiative = st.number_input(
                        "Initiative",
                        min_value=0,
                        value=10,
                        step=1,
                        key=f"encounter-add-initiative::{active_scene.id}",
                    )
                    armor_class = st.number_input(
                        "RK",
                        min_value=0,
                        value=10,
                        step=1,
                        key=f"encounter-add-ac::{active_scene.id}",
                    )
                    if st.form_submit_button("Combatant speichern") and name.strip():
                        _add_combatant(
                            session_dir,
                            active_scene.id,
                            monster_links,
                            name=name,
                            side=side,
                            max_hp=int(max_hp),
                            initiative=int(initiative),
                            armor_class=int(armor_class),
                        )
                        st.rerun()
