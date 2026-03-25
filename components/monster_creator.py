from pathlib import Path
import re

import streamlit as st


MONSTER_CREATOR_FEATURE_NAME = "Monster Ersteller"
MONSTER_UNKNOWN_VALUE = "unbekannt"
MONSTER_FOUNDATION_OPTIONS = [
    "#Homebrew",
    "#Book",
    "#Online",
    "#Homebrew #Book",
    "#Homebrew #Online",
    "#Book #Online",
    "#Homebrew #Book #Online",
]
MONSTER_ALIGNMENT_OPTIONS = [
    "Frei eingeben",
    "Rechtschaffen Gut",
    "Neutral Gut",
    "Chaotisch Gut",
    "Rechtschaffen Neutral",
    "Neutral",
    "Chaotisch Neutral",
    "Rechtschaffen Boese",
    "Neutral Boese",
    "Chaotisch Boese",
]
MONSTER_TYPE_OPTIONS = [
    "Frei eingeben",
    "Humanoid",
    "Untoter",
    "Unhold",
    "Bestie",
    "Konstrukt",
    "Drache",
    "Elementar",
    "Feenwesen",
    "Monstrositaet",
]
MONSTER_ORIGIN_OPTIONS = [
    "Frei eingeben",
    "Ardanos",
    "Drakmora",
    "Elmrath",
    "Mariven",
    "Schwarzklamm",
    "Vaylen",
    "Hoelle",
    "Nebelhaefen",
]
MONSTER_ROLE_OPTIONS = [
    "Frei eingeben",
    "Soldat",
    "Assassine",
    "Beschwoerer",
    "Kontrollzauberer",
    "Bestie",
    "Boss",
    "Elite",
    "Diener",
    "Heiler",
]
MONSTER_STAT_FIELDS = (
    ("str", "Str"),
    ("dex", "Ges"),
    ("con", "Kon"),
    ("int", "Int"),
    ("wis", "Wei"),
    ("cha", "Cha"),
)
MONSTER_ACTION_TYPE_OPTIONS = [
    "standard",
    "special",
    "bonus",
    "reaction",
    "legendary",
    "passive",
]
MONSTER_ACTION_CATEGORY_OPTIONS = [
    "melee",
    "ranged",
    "spell",
    "aura",
    "control",
    "summon",
    "utility",
]
MONSTER_CATALOG_STRATEGIES = [
    "",
    "bruiser",
    "controller",
    "skirmisher",
    "artillery",
    "summoner",
    "boss",
]
MONSTER_CATALOG_TAG_OPTIONS = [
    "BURST",
    "CONTROL",
    "TANK",
    "MOBIL",
    "FERNKAMPF",
    "BESCHWOERUNG",
    "FLAECHE",
    "DEBUFF",
    "HEIMLICH",
]
MONSTER_DEFENSE_OPTIONS = [
    "Saeure",
    "Blitz",
    "Donner",
    "Feuer",
    "Gift",
    "Kaelte",
    "Nekrotisch",
    "Psychisch",
    "Strahlend",
    "Wucht",
    "Stich",
    "Hieb",
    "Wucht von nicht-magischen Waffen",
    "Stich von nicht-magischen Waffen",
    "Hieb von nicht-magischen Waffen",
    "Wucht, Stich und Hieb von nicht-magischen Waffen",
]


def set_to_monster_creator_view() -> None:
    st.session_state["db_flag"] = True
    st.session_state["db"] = MONSTER_CREATOR_FEATURE_NAME


def monster_creator_is_admin() -> bool:
    user = st.session_state.get("user")
    return bool(user and getattr(user.role, "value", None) == "GameMaster")


def _resolved_select_value(select_key: str, custom_key: str) -> str:
    selected_value = st.session_state.get(select_key, "Frei eingeben")
    if selected_value == "Frei eingeben":
        return st.session_state.get(custom_key, "").strip()
    return selected_value


def _monster_export_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "World" / "Bestiarium"


def _sanitize_filename(name: str) -> str:
    normalized = name.strip() or "Unbenanntes Monster"
    normalized = re.sub(r"[^A-Za-z0-9 _().-]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or "Unbenanntes Monster"


def _modifier(score: int) -> str:
    value = (score - 10) // 2
    return f"{value:+d}"


def _format_stat(score: int) -> str:
    return f"{score} ({_modifier(score)})"


def _format_bonus(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith(("+", "-")):
        return cleaned
    return f"+{cleaned}"


def _text_or_dash(value: str) -> str:
    cleaned = value.strip()
    return cleaned if cleaned else "-"


def _multiline_or_dash(value: str) -> str:
    cleaned = value.strip()
    return cleaned if cleaned else "-"


def _format_selected_values(values: list[str] | tuple[str, ...] | str) -> str:
    if isinstance(values, str):
        cleaned = values.strip()
        return cleaned if cleaned else "-"
    filtered_values = [
        value.strip() for value in values if isinstance(value, str) and value.strip()
    ]
    return ", ".join(filtered_values) if filtered_values else "-"


def _parse_spell_names(raw_value: object) -> list[str]:
    if isinstance(raw_value, list):
        return [
            value.strip()
            for value in raw_value
            if isinstance(value, str) and value.strip()
        ]
    if not isinstance(raw_value, str):
        return []

    normalized = raw_value.replace("\r", "\n")
    entries = re.split(r"[,\n]", normalized)
    cleaned_entries = []
    for entry in entries:
        cleaned = entry.strip()
        if cleaned.startswith("- "):
            cleaned = cleaned[2:].strip()
        if cleaned.startswith("[[") and cleaned.endswith("]]"):
            cleaned = cleaned[2:-2].strip()
        if cleaned:
            cleaned_entries.append(cleaned)
    return cleaned_entries


def _list_from_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _format_spell_list(value: list[str] | tuple[str, ...] | str) -> str:
    spells = _parse_spell_names(value)
    if not spells:
        return "- [[Zaubername]]"
    return "\n".join(f"- [[{spell}]]" for spell in spells)


def _normalize_multiselect_state(session_key: str) -> None:
    raw_value = st.session_state.get(session_key, [])
    if isinstance(raw_value, list):
        st.session_state[session_key] = [
            item.strip() for item in raw_value if isinstance(item, str) and item.strip()
        ]
        return
    if isinstance(raw_value, str):
        st.session_state[session_key] = [
            item.strip() for item in raw_value.split(",") if item.strip()
        ]
        return
    st.session_state[session_key] = []


def _normalize_spell_selection_state(session_key: str) -> None:
    st.session_state[session_key] = _parse_spell_names(
        st.session_state.get(session_key, [])
    )


def _spell_level_value(raw_value: object) -> int | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if not text:
        return None
    match = re.search(r"\d+", text)
    if match:
        return int(match.group())
    lowered = text.casefold()
    if "zaubertrick" in lowered or "cantrip" in lowered:
        return 0
    return None


def _all_spell_records() -> list[tuple[str, int | None]]:
    spell_df = st.session_state.get("Zauberarchiv")
    if spell_df is None or not hasattr(spell_df, "iterrows"):
        return []

    records = []
    for _index, row in spell_df.iterrows():
        name = str(row.get("Name", "")).strip()
        if not name:
            continue
        records.append((name, _spell_level_value(row.get("Grad"))))
    return records


def _spell_options_for_level(
    level: int, selected: list[str] | None = None
) -> list[str]:
    options = [
        name for name, spell_level in _all_spell_records() if spell_level == level
    ]
    if selected:
        options.extend(selected)
    return sorted(dict.fromkeys(options), key=str.casefold)


def _all_spell_options(selected: list[str] | None = None) -> list[str]:
    options = [name for name, _level in _all_spell_records()]
    if selected:
        options.extend(selected)
    return sorted(dict.fromkeys(options), key=str.casefold)


def _spell_metadata_by_name(spell_name: str) -> dict[str, str]:
    if not spell_name.strip():
        return {}

    spell_df = st.session_state.get("Zauberarchiv")
    if spell_df is None or not hasattr(spell_df, "iterrows"):
        return {}

    for _index, row in spell_df.iterrows():
        name = str(row.get("Name", "")).strip()
        if name != spell_name.strip():
            continue
        return {
            "name": name,
            "grad": str(row.get("Grad", "")).strip(),
            "schule": str(row.get("Schule", "")).strip(),
            "konzentration": str(row.get("Konzentration", "")).strip(),
            "komponenten": str(row.get("Komponenten", "")).strip(),
        }

    return {}


def _known_monster_spell_options(selected: list[str] | None = None) -> list[str]:
    known_spells = list(st.session_state.get("monster_creator_cantrips", []))
    for level in range(1, 10):
        known_spells.extend(
            st.session_state.get(f"monster_creator_spells_level_{level}", [])
        )
    known_spells.extend(st.session_state.get("monster_creator_spells_per_day", []))
    if selected:
        known_spells.extend(selected)
    return sorted(
        dict.fromkeys(
            spell for spell in known_spells if isinstance(spell, str) and spell.strip()
        ),
        key=str.casefold,
    )


def _new_action_id() -> int:
    next_id = int(st.session_state.get("monster_creator_next_action_id", 1))
    st.session_state["monster_creator_next_action_id"] = next_id + 1
    return next_id


def _empty_monster_action(action_id: int | None = None) -> dict[str, str | int]:
    resolved_action_id = action_id if action_id is not None else _new_action_id()
    return {
        "id": resolved_action_id,
        "name": "",
        "linked_spell": "",
        "action_type": "standard",
        "category": "melee",
        "usage_limit": "",
        "attack_bonus": "",
        "save_ability": "",
        "save_dc": "",
        "range_text": "",
        "target_text": "",
        "damage_text": "",
        "effect_text": "",
        "notes": "",
    }


def _action_widget_key(action_id: int, field_name: str) -> str:
    return f"monster_creator_action_{field_name}_{action_id}"


def _sync_action_widget_state(action: dict[str, str | int]) -> None:
    action_id_raw = action.get("id")
    if not isinstance(action_id_raw, int):
        action_id_raw = _new_action_id()
        action["id"] = action_id_raw
    action_id = int(action_id_raw)
    field_defaults = {
        "name": str(action.get("name", "")),
        "linked_spell": str(action.get("linked_spell", "")),
        "action_type": str(action.get("action_type", "standard")),
        "category": str(action.get("category", "melee")),
        "usage_limit": str(action.get("usage_limit", "")),
        "attack_bonus": str(action.get("attack_bonus", "")),
        "save_ability": str(action.get("save_ability", "")),
        "save_dc": str(action.get("save_dc", "")),
        "range_text": str(action.get("range_text", "")),
        "target_text": str(action.get("target_text", "")),
        "damage_text": str(action.get("damage_text", "")),
        "effect_text": str(action.get("effect_text", "")),
        "notes": str(action.get("notes", "")),
    }
    for field_name, value in field_defaults.items():
        widget_key = _action_widget_key(action_id, field_name)
        if widget_key not in st.session_state:
            st.session_state[widget_key] = value


def _normalize_action(action: object) -> dict[str, str | int]:
    if not isinstance(action, dict):
        return _empty_monster_action()

    normalized_action = {
        "id": action.get("id"),
        "name": str(action.get("name", "")),
        "linked_spell": str(action.get("linked_spell", "")),
        "action_type": str(action.get("action_type", "standard")),
        "category": str(action.get("category", "melee")),
        "usage_limit": str(action.get("usage_limit", "")),
        "attack_bonus": str(action.get("attack_bonus", "")),
        "save_ability": str(action.get("save_ability", "")),
        "save_dc": str(action.get("save_dc", "")),
        "range_text": str(action.get("range_text", "")),
        "target_text": str(action.get("target_text", "")),
        "damage_text": str(action.get("damage_text", "")),
        "effect_text": str(action.get("effect_text", "")),
        "notes": str(action.get("notes", "")),
    }

    if not isinstance(normalized_action["id"], int):
        normalized_action["id"] = _new_action_id()

    if normalized_action["action_type"] not in MONSTER_ACTION_TYPE_OPTIONS:
        normalized_action["action_type"] = "standard"
    if normalized_action["category"] not in MONSTER_ACTION_CATEGORY_OPTIONS:
        normalized_action["category"] = "melee"

    return normalized_action


def _normalize_actions_state() -> None:
    actions_raw = st.session_state.get("monster_creator_actions", [])
    if not isinstance(actions_raw, list) or not actions_raw:
        st.session_state["monster_creator_actions"] = [_empty_monster_action()]
        return

    normalized_actions = [_normalize_action(action) for action in actions_raw]
    st.session_state["monster_creator_actions"] = normalized_actions


def _ensure_monster_creator_state() -> None:
    defaults = {
        "monster_creator_name": "",
        "monster_creator_foundation": MONSTER_FOUNDATION_OPTIONS[0],
        "monster_creator_cr": "",
        "monster_creator_type": MONSTER_TYPE_OPTIONS[0],
        "monster_creator_type_custom": "",
        "monster_creator_origin": MONSTER_ORIGIN_OPTIONS[0],
        "monster_creator_origin_custom": "",
        "monster_creator_role": MONSTER_ROLE_OPTIONS[0],
        "monster_creator_role_custom": "",
        "monster_creator_alias": "",
        "monster_creator_age": MONSTER_UNKNOWN_VALUE,
        "monster_creator_alignment": MONSTER_ALIGNMENT_OPTIONS[0],
        "monster_creator_alignment_custom": "",
        "monster_creator_languages": "",
        "monster_creator_traits": "",
        "monster_creator_ideals": "",
        "monster_creator_bonds": "",
        "monster_creator_ac": 10,
        "monster_creator_armor_text": "",
        "monster_creator_initiative": 0,
        "monster_creator_hp": 1,
        "monster_creator_hit_dice": "",
        "monster_creator_passive_perception": 10,
        "monster_creator_weapons": "",
        "monster_creator_move_walk": 9,
        "monster_creator_move_fly": 0,
        "monster_creator_move_swim": 0,
        "monster_creator_move_climb": 0,
        "monster_creator_move_burrow": 0,
        "monster_creator_skill_lines": "",
        "monster_creator_immunities": [],
        "monster_creator_resistances": [],
        "monster_creator_vulnerabilities": [],
        "monster_creator_condition_immunities": "",
        "monster_creator_senses": "",
        "monster_creator_weaknesses": [],
        "monster_creator_has_spellcasting": False,
        "monster_creator_spellcasting_ability": "Charisma",
        "monster_creator_spell_dc": 10,
        "monster_creator_spell_attack_bonus": 0,
        "monster_creator_spellcaster_level": "",
        "monster_creator_spell_slots": "",
        "monster_creator_cantrips": [],
        "monster_creator_spells_level_1": [],
        "monster_creator_spells_level_2": [],
        "monster_creator_spells_level_3": [],
        "monster_creator_spells_level_4": [],
        "monster_creator_spells_level_5": [],
        "monster_creator_spells_level_6": [],
        "monster_creator_spells_level_7": [],
        "monster_creator_spells_level_8": [],
        "monster_creator_spells_level_9": [],
        "monster_creator_spells_per_day": [],
        "monster_creator_special_spells": "",
        "monster_creator_catalog_enabled": False,
        "monster_creator_catalog_key": "",
        "monster_creator_strategy_override": "",
        "monster_creator_tags_override": [],
        "monster_creator_threat_override": 0.0,
        "monster_creator_action_override": 0.0,
        "monster_creator_volatility_override": 0.0,
        "monster_creator_legendary_actions_override": False,
        "monster_creator_legendary_resistances_override": False,
        "monster_creator_phase_change_override": False,
        "monster_creator_summons_override": False,
        "monster_creator_catalog_hint": "",
        "monster_creator_tactics": "",
        "monster_creator_equipment": "",
        "monster_creator_background": "",
        "monster_creator_quotes": "",
        "monster_creator_notes": "",
        "monster_creator_next_action_id": 1,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "monster_creator_actions" not in st.session_state:
        st.session_state["monster_creator_actions"] = [_empty_monster_action()]
    _normalize_actions_state()
    _normalize_multiselect_state("monster_creator_immunities")
    _normalize_multiselect_state("monster_creator_resistances")
    _normalize_multiselect_state("monster_creator_vulnerabilities")
    _normalize_multiselect_state("monster_creator_weaknesses")
    _normalize_spell_selection_state("monster_creator_cantrips")
    for level in range(1, 10):
        _normalize_spell_selection_state(f"monster_creator_spells_level_{level}")
    _normalize_spell_selection_state("monster_creator_spells_per_day")

    for key, _label in MONSTER_STAT_FIELDS:
        session_key = f"monster_creator_{key}"
        if session_key not in st.session_state:
            st.session_state[session_key] = 10
        save_key = f"monster_creator_save_{key}"
        if save_key not in st.session_state:
            st.session_state[save_key] = ""


def _monster_profile_values() -> dict[str, object]:
    stats = {
        key: int(st.session_state.get(f"monster_creator_{key}", 10))
        for key, _ in MONSTER_STAT_FIELDS
    }
    saves = {
        key: st.session_state.get(f"monster_creator_save_{key}", "").strip()
        for key, _ in MONSTER_STAT_FIELDS
    }
    actions = st.session_state.get("monster_creator_actions", [])
    return {
        "name": st.session_state.get("monster_creator_name", "").strip(),
        "foundation": st.session_state.get(
            "monster_creator_foundation", MONSTER_FOUNDATION_OPTIONS[0]
        ),
        "cr": st.session_state.get("monster_creator_cr", "").strip(),
        "type": _resolved_select_value(
            "monster_creator_type", "monster_creator_type_custom"
        ),
        "origin": _resolved_select_value(
            "monster_creator_origin", "monster_creator_origin_custom"
        ),
        "role": _resolved_select_value(
            "monster_creator_role", "monster_creator_role_custom"
        ),
        "alias": st.session_state.get("monster_creator_alias", "").strip(),
        "age": st.session_state.get("monster_creator_age", "").strip(),
        "alignment": _resolved_select_value(
            "monster_creator_alignment", "monster_creator_alignment_custom"
        ),
        "languages": st.session_state.get("monster_creator_languages", "").strip(),
        "traits": st.session_state.get("monster_creator_traits", "").strip(),
        "ideals": st.session_state.get("monster_creator_ideals", "").strip(),
        "bonds": st.session_state.get("monster_creator_bonds", "").strip(),
        "ac": int(st.session_state.get("monster_creator_ac", 10)),
        "armor_text": st.session_state.get("monster_creator_armor_text", "").strip(),
        "initiative": int(st.session_state.get("monster_creator_initiative", 0)),
        "hp": int(st.session_state.get("monster_creator_hp", 1)),
        "hit_dice": st.session_state.get("monster_creator_hit_dice", "").strip(),
        "passive_perception": int(
            st.session_state.get("monster_creator_passive_perception", 10)
        ),
        "weapons": st.session_state.get("monster_creator_weapons", "").strip(),
        "movement": {
            "walk": int(st.session_state.get("monster_creator_move_walk", 0)),
            "fly": int(st.session_state.get("monster_creator_move_fly", 0)),
            "swim": int(st.session_state.get("monster_creator_move_swim", 0)),
            "climb": int(st.session_state.get("monster_creator_move_climb", 0)),
            "burrow": int(st.session_state.get("monster_creator_move_burrow", 0)),
        },
        "stats": stats,
        "saves": saves,
        "skills": st.session_state.get("monster_creator_skill_lines", "").strip(),
        "immunities": list(st.session_state.get("monster_creator_immunities", [])),
        "resistances": list(st.session_state.get("monster_creator_resistances", [])),
        "vulnerabilities": list(
            st.session_state.get("monster_creator_vulnerabilities", [])
        ),
        "condition_immunities": st.session_state.get(
            "monster_creator_condition_immunities", ""
        ).strip(),
        "senses": st.session_state.get("monster_creator_senses", "").strip(),
        "weaknesses": list(st.session_state.get("monster_creator_weaknesses", [])),
        "actions": actions,
        "has_spellcasting": bool(
            st.session_state.get("monster_creator_has_spellcasting", False)
        ),
        "spellcasting_ability": st.session_state.get(
            "monster_creator_spellcasting_ability", "Charisma"
        ),
        "spell_dc": int(st.session_state.get("monster_creator_spell_dc", 10)),
        "spell_attack_bonus": int(
            st.session_state.get("monster_creator_spell_attack_bonus", 0)
        ),
        "spellcaster_level": st.session_state.get(
            "monster_creator_spellcaster_level", ""
        ).strip(),
        "spell_slots": st.session_state.get("monster_creator_spell_slots", "").strip(),
        "cantrips": list(st.session_state.get("monster_creator_cantrips", [])),
        "spells_by_level": {
            level: list(
                st.session_state.get(f"monster_creator_spells_level_{level}", [])
            )
            for level in range(1, 10)
        },
        "spells_per_day": list(
            st.session_state.get("monster_creator_spells_per_day", [])
        ),
        "special_spells": st.session_state.get(
            "monster_creator_special_spells", ""
        ).strip(),
        "catalog_enabled": bool(
            st.session_state.get("monster_creator_catalog_enabled", False)
        ),
        "catalog_key": st.session_state.get("monster_creator_catalog_key", "").strip(),
        "strategy_override": st.session_state.get(
            "monster_creator_strategy_override", ""
        ).strip(),
        "tags_override": list(
            st.session_state.get("monster_creator_tags_override", [])
        ),
        "threat_override": float(
            st.session_state.get("monster_creator_threat_override", 0.0)
        ),
        "action_override": float(
            st.session_state.get("monster_creator_action_override", 0.0)
        ),
        "volatility_override": float(
            st.session_state.get("monster_creator_volatility_override", 0.0)
        ),
        "legendary_actions_override": bool(
            st.session_state.get("monster_creator_legendary_actions_override", False)
        ),
        "legendary_resistances_override": bool(
            st.session_state.get(
                "monster_creator_legendary_resistances_override", False
            )
        ),
        "phase_change_override": bool(
            st.session_state.get("monster_creator_phase_change_override", False)
        ),
        "summons_override": bool(
            st.session_state.get("monster_creator_summons_override", False)
        ),
        "catalog_hint": st.session_state.get(
            "monster_creator_catalog_hint", ""
        ).strip(),
        "tactics": st.session_state.get("monster_creator_tactics", "").strip(),
        "equipment": st.session_state.get("monster_creator_equipment", "").strip(),
        "background": st.session_state.get("monster_creator_background", "").strip(),
        "quotes": st.session_state.get("monster_creator_quotes", "").strip(),
        "notes": st.session_state.get("monster_creator_notes", "").strip(),
    }


def _format_movement(movement: dict[str, int]) -> str:
    labels = {
        "walk": "m",
        "fly": "m Flug",
        "swim": "m Schwimmen",
        "climb": "m Klettern",
        "burrow": "m Graben",
    }
    parts = []
    for key in ("walk", "fly", "swim", "climb", "burrow"):
        value = int(movement.get(key, 0))
        if value > 0:
            parts.append(f"{value}{labels[key]}")
    return ", ".join(parts) if parts else "-"


def _render_actions_section(actions: list[dict[str, str]], action_type: str) -> str:
    filtered_actions = [
        action
        for action in actions
        if action.get("action_type") == action_type
        and (action.get("name", "").strip() or action.get("linked_spell", "").strip())
    ]
    if not filtered_actions:
        return ""

    section_titles = {
        "standard": "### Standard",
        "special": "### Spezialfaehigkeiten",
        "bonus": "### Bonusaktionen",
        "reaction": "### Reaktionen",
        "legendary": "### Legendenaktionen",
        "passive": "### Passive Faehigkeiten",
    }
    lines = [section_titles[action_type], ""]
    for action in filtered_actions:
        action_name = (
            action.get("name", "").strip() or action.get("linked_spell", "").strip()
        )
        suffix = (
            f" ({action['usage_limit']})"
            if action.get("usage_limit", "").strip()
            else ""
        )
        lines.append(f"- **{action_name or 'Aktionsname'}{suffix}:**")
        detail_lines = []
        if action.get("linked_spell", "").strip():
            detail_lines.append(f"Zauber: [[{action['linked_spell'].strip()}]]")
        if action.get("attack_bonus", "").strip():
            detail_lines.append(
                f"Angriff: {_format_bonus(action['attack_bonus'])} zum Treffen"
            )
        if action.get("save_ability", "").strip() and action.get("save_dc", "").strip():
            detail_lines.append(
                f"Rettungswurf: {action['save_ability'].strip()} SG {action['save_dc'].strip()}"
            )
        if action.get("range_text", "").strip():
            detail_lines.append(f"Reichweite: {action['range_text'].strip()}")
        if action.get("target_text", "").strip():
            detail_lines.append(f"Ziel: {action['target_text'].strip()}")
        if action.get("damage_text", "").strip():
            detail_lines.append(f"Schaden: {action['damage_text'].strip()}")
        if action.get("effect_text", "").strip():
            detail_lines.append(action["effect_text"].strip())
        if action.get("notes", "").strip():
            detail_lines.append(action["notes"].strip())

        if detail_lines:
            lines.extend(f"  - {detail}" for detail in detail_lines)
        else:
            lines.append("  - Effektbeschreibung")
        lines.append("")
    return "\n".join(lines).strip()


def _render_spellcasting_section(profile: dict[str, object]) -> str:
    if not profile["has_spellcasting"]:
        return ""

    lines = ["### Zauber", ""]
    caster_header = str(profile["spellcaster_level"]).strip()
    if caster_header:
        lines.append(
            f"{caster_header} ({profile['spellcasting_ability']}-basiert, SG {profile['spell_dc']}, {_format_bonus(str(profile['spell_attack_bonus']))} Angriff)."
        )
    else:
        lines.append(
            f"{profile['spellcasting_ability']}-basiert (SG {profile['spell_dc']}, {_format_bonus(str(profile['spell_attack_bonus']))} Angriff)."
        )
    lines.append("")
    lines.append(f"**Zauberplaetze:** {_text_or_dash(str(profile['spell_slots']))}")
    lines.append("")
    lines.append("**Zaubertricks:**")
    lines.append(_format_spell_list(profile["cantrips"]))
    lines.append("")

    for level, spells in profile["spells_by_level"].items():
        if spells:
            lines.append(f"**{level}. Grad:**")
            lines.append(_format_spell_list(spells))
            lines.append("")

    if profile["spells_per_day"]:
        lines.append("**Pro Tag:**")
        lines.append(_format_spell_list(profile["spells_per_day"]))
        lines.append("")

    if profile["special_spells"]:
        lines.append("**Sonderzauber:**")
        lines.append(_multiline_or_dash(str(profile["special_spells"])))

    return "\n".join(lines).strip()


def _render_catalog_metadata(profile: dict[str, object]) -> str:
    if not profile["catalog_enabled"]:
        return ""

    lines = ["## Katalog-Metadaten", ""]
    fields = [
        ("Katalog-Key", str(profile["catalog_key"])),
        ("Strategie-Override", str(profile["strategy_override"])),
        ("Tags-Override", ", ".join(profile["tags_override"])),
        (
            "Threat-Override",
            str(profile["threat_override"]) if profile["threat_override"] else "",
        ),
        (
            "Action-Override",
            str(profile["action_override"]) if profile["action_override"] else "",
        ),
        (
            "Volatilitaet-Override",
            (
                str(profile["volatility_override"])
                if profile["volatility_override"]
                else ""
            ),
        ),
        (
            "Legendaere Aktionen-Override",
            "ja" if profile["legendary_actions_override"] else "",
        ),
        (
            "Legendaere Resistenzen-Override",
            "ja" if profile["legendary_resistances_override"] else "",
        ),
        ("Phasenwechsel-Override", "ja" if profile["phase_change_override"] else ""),
        ("Beschwoerung-Override", "ja" if profile["summons_override"] else ""),
        ("Katalog-Hinweis", str(profile["catalog_hint"])),
    ]
    for label, value in fields:
        if value:
            lines.append(f"- **{label}:** {value}")

    return "\n".join(lines).strip()


def _render_export_markdown() -> str:
    profile = _monster_profile_values()
    name = str(profile["name"]) or "Monstername"
    movement_text = _format_movement(profile["movement"])
    catalog_section = _render_catalog_metadata(profile)
    actions = profile["actions"]
    action_sections = [
        _render_actions_section(actions, "standard"),
        _render_actions_section(actions, "special"),
        _render_actions_section(actions, "bonus"),
        _render_actions_section(actions, "reaction"),
        _render_spellcasting_section(profile),
        _render_actions_section(actions, "legendary"),
        _render_actions_section(actions, "passive"),
    ]
    action_sections = [section for section in action_sections if section]

    table_header = "| Wert | Str | Ges | Kon | Int | Wei | Cha |"
    table_rule = "| ---- | --- | --- | --- | --- | --- | --- |"
    attribute_row = (
        "| Attribut | "
        + " | ".join(
            _format_stat(profile["stats"][key]) for key, _label in MONSTER_STAT_FIELDS
        )
        + " |"
    )
    save_row = (
        "| Rettung | "
        + " | ".join(
            (
                _format_bonus(str(profile["saves"][key]))
                if str(profile["saves"][key]).strip()
                else "-"
            )
            for key, _label in MONSTER_STAT_FIELDS
        )
        + " |"
    )

    lines = [
        f"# {name}",
        "",
        f"- **Grundlage:** {profile['foundation']}",
        f"- **Stufe/Herausfordungsgrad:** {_text_or_dash(str(profile['cr']))}",
        f"- **Volk:** {_text_or_dash(str(profile['type']))}",
        f"- **Herkunft:** {_text_or_dash(str(profile['origin']))}",
        f"- **Klasse:** {_text_or_dash(str(profile['role']))}",
        f"- **Alias:** {_text_or_dash(str(profile['alias']))}",
        f"- **Alter:** {_text_or_dash(str(profile['age']))}",
        f"- **Gesinnung:** {_text_or_dash(str(profile['alignment']))}",
        f"- **Sprachen:** {_text_or_dash(str(profile['languages']))}",
        f"- **Merkmale:** {_text_or_dash(str(profile['traits']))}",
    ]

    if profile["ideals"]:
        lines.append(f"- **Ideale:** {profile['ideals']}")
    if profile["bonds"]:
        lines.append(f"- **Bindungen:** {profile['bonds']}")

    lines.extend(["", "---", ""])
    if catalog_section:
        lines.append(catalog_section)
        lines.extend(["", "---", ""])

    lines.extend(
        [
            "## Eigenschaften",
            "",
            f"- **Ruestungsklasse (RK)/Ruestung:** {profile['ac']} {str(profile['armor_text']).strip()}".rstrip(),
            f"- **Waffen:** {_text_or_dash(str(profile['weapons']))}",
            f"- **Initiative:** {profile['initiative']:+d}",
            f"- **Bewegung:** {movement_text}",
            f"- **Trefferpunkte:** {profile['hp']}",
            f"- **Trefferwuerfel:** {_text_or_dash(str(profile['hit_dice']))}",
            f"- **Passive Wahrnehmung:** {profile['passive_perception']}",
            f"- **Fertigkeiten:** {_multiline_or_dash(str(profile['skills']))}",
            "",
            table_header,
            table_rule,
            attribute_row,
            save_row,
            "",
            f"- **Immunitaeten:** {_format_selected_values(profile['immunities'])}",
            f"- **Resistenzen:** {_format_selected_values(profile['resistances'])}",
            f"- **Verwundbarkeiten:** {_format_selected_values(profile['vulnerabilities'])}",
            f"- **Zustandsimmunitaeten:** {_multiline_or_dash(str(profile['condition_immunities']))}",
            f"- **Sinne:** {_multiline_or_dash(str(profile['senses']))}",
            f"- **Schwaechen:** {_format_selected_values(profile['weaknesses'])}",
            "",
            "---",
            "",
            "## Aktionen",
            "",
        ]
    )

    if action_sections:
        lines.append("\n\n".join(action_sections))
    else:
        lines.extend(["### Standard", "", "- **Mehrfachangriff:**", ""])

    lines.extend(
        [
            "",
            "---",
            "",
            "## Taktik",
            "",
            _multiline_or_dash(str(profile["tactics"])),
            "",
            "---",
            "",
            "## Ausruestung",
            "",
            _multiline_or_dash(str(profile["equipment"])),
            "",
            "---",
            "",
            "## Hintergrund",
            "",
            _multiline_or_dash(str(profile["background"])),
            "",
            "---",
            "",
            "## Zitate",
            "",
            _multiline_or_dash(str(profile["quotes"])),
        ]
    )

    if profile["notes"]:
        lines.extend(["", "---", "", "## Notizen", "", str(profile["notes"])])

    return "\n".join(lines).strip() + "\n"


def _validate_monster_profile(profile: dict[str, object]) -> list[str]:
    warnings = []
    if not profile["name"]:
        warnings.append("Name fehlt.")
    if not profile["cr"]:
        warnings.append("Stufe oder Herausforderungsgrad fehlt.")
    if not any(
        action.get("name", "").strip() or action.get("linked_spell", "").strip()
        for action in profile["actions"]
    ):
        warnings.append("Es ist noch keine Aktion angelegt.")
    if (
        profile["has_spellcasting"]
        and not profile["cantrips"]
        and not any(profile["spells_by_level"].values())
        and not profile["spells_per_day"]
    ):
        warnings.append(
            "Zauberwirken ist aktiv, aber es sind noch keine Zauber eingetragen."
        )
    if profile["legendary_actions_override"] and not any(
        action.get("action_type") == "legendary"
        and (action.get("name", "").strip() or action.get("linked_spell", "").strip())
        for action in profile["actions"]
    ):
        warnings.append(
            "Legendaere Aktionen sind markiert, aber keine legendaeren Aktionen wurden erfasst."
        )
    return warnings


def _export_monster_markdown() -> tuple[bool, str]:
    export_dir = _monster_export_directory()
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = (
        f"{_sanitize_filename(st.session_state.get('monster_creator_name', ''))}.md"
    )
    export_path = export_dir / file_name
    if export_path.exists():
        return False, f"Datei existiert bereits: {export_path.name}"
    export_path.write_text(_render_export_markdown(), encoding="utf-8")
    return True, str(export_path)


def _add_action() -> None:
    st.session_state["monster_creator_actions"] = st.session_state.get(
        "monster_creator_actions", []
    ) + [_empty_monster_action()]


def _remove_action(index: int) -> None:
    actions = list(st.session_state.get("monster_creator_actions", []))
    if len(actions) <= 1:
        actions = [_empty_monster_action()]
    else:
        removed_action = actions.pop(index)
        removed_action_id = int(removed_action.get("id", 0))
        for field_name in (
            "name",
            "linked_spell",
            "action_type",
            "category",
            "usage_limit",
            "attack_bonus",
            "save_ability",
            "save_dc",
            "range_text",
            "target_text",
            "damage_text",
            "effect_text",
            "notes",
        ):
            st.session_state.pop(
                _action_widget_key(removed_action_id, field_name), None
            )
    st.session_state["monster_creator_actions"] = actions


def monster_creator_view() -> None:
    set_to_monster_creator_view()
    if not monster_creator_is_admin():
        st.warning("Der Monster-Ersteller ist nur fuer Spielleiter verfuegbar.")
        return

    _ensure_monster_creator_state()

    st.subheader("Monster Ersteller")
    st.caption("Erfasst Kernwerte, Aktionen und Export fuer Bestiarium-Eintraege.")

    form_col, preview_col = st.columns([3, 4], vertical_alignment="top")

    with form_col:
        with st.container(border=True):
            st.markdown("**Identitaet**")
            st.text_input(
                "Name",
                key="monster_creator_name",
                placeholder="Zum Beispiel: Lord Malvurax",
            )
            row = st.columns(3)
            row[0].selectbox(
                "Grundlage",
                MONSTER_FOUNDATION_OPTIONS,
                key="monster_creator_foundation",
            )
            row[1].text_input(
                "Stufe / CR",
                key="monster_creator_cr",
                placeholder="Zum Beispiel: 7",
            )
            row[2].text_input("Alias", key="monster_creator_alias")

            row = st.columns(3)
            row[0].selectbox(
                "Volk / Typ", MONSTER_TYPE_OPTIONS, key="monster_creator_type"
            )
            if st.session_state.get("monster_creator_type") == "Frei eingeben":
                row[0].text_input("Typ frei", key="monster_creator_type_custom")
            row[1].selectbox(
                "Herkunft", MONSTER_ORIGIN_OPTIONS, key="monster_creator_origin"
            )
            if st.session_state.get("monster_creator_origin") == "Frei eingeben":
                row[1].text_input("Herkunft frei", key="monster_creator_origin_custom")
            row[2].selectbox(
                "Klasse / Rolle", MONSTER_ROLE_OPTIONS, key="monster_creator_role"
            )
            if st.session_state.get("monster_creator_role") == "Frei eingeben":
                row[2].text_input("Rolle frei", key="monster_creator_role_custom")

            row = st.columns(3)
            row[0].text_input("Alter", key="monster_creator_age")
            row[1].selectbox(
                "Gesinnung",
                MONSTER_ALIGNMENT_OPTIONS,
                key="monster_creator_alignment",
            )
            if st.session_state.get("monster_creator_alignment") == "Frei eingeben":
                row[1].text_input(
                    "Gesinnung frei", key="monster_creator_alignment_custom"
                )
            row[2].text_input("Sprachen", key="monster_creator_languages")

            st.text_area(
                "Merkmale",
                key="monster_creator_traits",
                height=80,
                placeholder="Kurze Stichworte, Auftreten, markante Eigenschaften",
            )
            with st.expander("Optionale Kopfdaten"):
                st.text_area("Ideale", key="monster_creator_ideals", height=80)
                st.text_area("Bindungen", key="monster_creator_bonds", height=80)

        with st.container(border=True):
            st.markdown("**Kampfkern**")
            row = st.columns(4)
            row[0].number_input(
                "RK", min_value=1, max_value=40, key="monster_creator_ac"
            )
            row[1].number_input(
                "Initiative",
                min_value=-10,
                max_value=20,
                key="monster_creator_initiative",
            )
            row[2].number_input(
                "Trefferpunkte",
                min_value=1,
                max_value=999,
                key="monster_creator_hp",
            )
            row[3].number_input(
                "Passive Wahrnehmung",
                min_value=1,
                max_value=40,
                key="monster_creator_passive_perception",
            )
            st.text_input(
                "Ruestungstext",
                key="monster_creator_armor_text",
                placeholder="Zum Beispiel: magische Kleidung oder natuerliche Ruestung",
            )
            row = st.columns(2)
            row[0].text_input(
                "Trefferwuerfel",
                key="monster_creator_hit_dice",
                placeholder="Zum Beispiel: 16W8 + 48",
            )
            row[1].text_input(
                "Waffen",
                key="monster_creator_weapons",
                placeholder="Zum Beispiel: Höllenspeer, Klauen, Langbogen",
            )

            st.markdown("**Bewegung**")
            row = st.columns(5)
            row[0].number_input(
                "Laufen", min_value=0, max_value=60, key="monster_creator_move_walk"
            )
            row[1].number_input(
                "Fliegen", min_value=0, max_value=60, key="monster_creator_move_fly"
            )
            row[2].number_input(
                "Schwimmen", min_value=0, max_value=60, key="monster_creator_move_swim"
            )
            row[3].number_input(
                "Klettern", min_value=0, max_value=60, key="monster_creator_move_climb"
            )
            row[4].number_input(
                "Graben", min_value=0, max_value=60, key="monster_creator_move_burrow"
            )

            st.markdown("**Attribute und Rettungen**")
            stat_cols = st.columns(6)
            save_cols = st.columns(6)
            for index, (key, label) in enumerate(MONSTER_STAT_FIELDS):
                stat_cols[index].number_input(
                    label,
                    min_value=1,
                    max_value=30,
                    key=f"monster_creator_{key}",
                )
                save_cols[index].text_input(
                    f"RW {label}", key=f"monster_creator_save_{key}", placeholder="+0"
                )

            with st.expander("Fertigkeiten und Verteidigungen", expanded=False):
                st.text_area(
                    "Fertigkeiten",
                    key="monster_creator_skill_lines",
                    height=100,
                    placeholder="Eine Zeile pro Eintrag, zum Beispiel:\nEinschuechtern +7\nArkana +5",
                )
                row = st.columns(2)
                row[0].multiselect(
                    "Immunitaeten",
                    MONSTER_DEFENSE_OPTIONS,
                    key="monster_creator_immunities",
                )
                row[1].multiselect(
                    "Resistenzen",
                    MONSTER_DEFENSE_OPTIONS,
                    key="monster_creator_resistances",
                )
                row = st.columns(2)
                row[0].multiselect(
                    "Verwundbarkeiten",
                    MONSTER_DEFENSE_OPTIONS,
                    key="monster_creator_vulnerabilities",
                )
                row[1].text_area(
                    "Zustandsimmunitaeten",
                    key="monster_creator_condition_immunities",
                    height=80,
                )
                row = st.columns(2)
                row[0].text_area("Sinne", key="monster_creator_senses", height=80)
                row[1].multiselect(
                    "Schwaechen",
                    MONSTER_DEFENSE_OPTIONS,
                    key="monster_creator_weaknesses",
                )

        with st.container(border=True):
            st.markdown("**Faehigkeiten**")
            st.button(
                "Aktion hinzufuegen", on_click=_add_action, use_container_width=True
            )
            for index, action in enumerate(
                st.session_state.get("monster_creator_actions", [])
            ):
                action_id = int(action.get("id", 0))
                _sync_action_widget_state(action)
                with st.expander(f"Aktion {index + 1}", expanded=index == 0):
                    row = st.columns([2, 1, 1])
                    row[1].selectbox(
                        "Typ",
                        MONSTER_ACTION_TYPE_OPTIONS,
                        key=_action_widget_key(action_id, "action_type"),
                    )
                    row[2].selectbox(
                        "Kategorie",
                        MONSTER_ACTION_CATEGORY_OPTIONS,
                        key=_action_widget_key(action_id, "category"),
                    )
                    action_category = st.session_state.get(
                        _action_widget_key(action_id, "category")
                    )
                    linked_spell_key = _action_widget_key(action_id, "linked_spell")
                    selected_linked_spell = st.session_state.get(linked_spell_key, "")
                    if action_category == "spell":
                        known_spell_options = [""] + _known_monster_spell_options(
                            [selected_linked_spell]
                        )
                        st.selectbox(
                            "Bekannter Zauber",
                            known_spell_options,
                            key=linked_spell_key,
                            help="Verlinkt einen bereits im Zauberblock ausgewaehlten Zauber direkt mit dieser Aktion.",
                        )
                        if len(known_spell_options) == 1:
                            st.caption(
                                "Noch keine Monster-Zauber ausgewaehlt. Du kannst die Aktion frei beschreiben oder erst den Zauberblock fuellen."
                            )
                        selected_linked_spell = st.session_state.get(
                            linked_spell_key, ""
                        )
                        if selected_linked_spell:
                            spell_metadata = _spell_metadata_by_name(
                                selected_linked_spell
                            )
                            if spell_metadata:
                                metadata_bits = []
                                if spell_metadata.get("grad"):
                                    metadata_bits.append(
                                        f"Grad {spell_metadata['grad']}"
                                    )
                                if spell_metadata.get("schule"):
                                    metadata_bits.append(spell_metadata["schule"])
                                if spell_metadata.get("konzentration"):
                                    metadata_bits.append(
                                        f"Konzentration: {spell_metadata['konzentration']}"
                                    )
                                if spell_metadata.get("komponenten"):
                                    metadata_bits.append(
                                        f"Komponenten: {spell_metadata['komponenten']}"
                                    )
                                st.caption(" | ".join(metadata_bits))
                            st.info(
                                f"Die Aktionsdetails werden aus [[{selected_linked_spell}]] referenziert. Sichtbar bleiben Nutzung und Zusatznotizen."
                            )
                        else:
                            row[0].text_input(
                                "Name",
                                key=_action_widget_key(action_id, "name"),
                            )
                    else:
                        row[0].text_input(
                            "Name",
                            key=_action_widget_key(action_id, "name"),
                        )

                    if action_category == "spell" and selected_linked_spell:
                        st.text_input(
                            "Nutzung",
                            key=_action_widget_key(action_id, "usage_limit"),
                            placeholder="1/Tag, 3/LR, pro Runde",
                        )
                        st.text_area(
                            "Zusatznotizen",
                            key=_action_widget_key(action_id, "notes"),
                            height=80,
                            placeholder="Zum Beispiel: Eroeffnet den Kampf damit oder nutzt den Zauber nur im Notfall.",
                        )
                    else:
                        row = st.columns(4)
                        row[0].text_input(
                            "Nutzung",
                            key=_action_widget_key(action_id, "usage_limit"),
                            placeholder="1/Tag, 3/LR, pro Runde",
                        )
                        row[1].text_input(
                            "Angriff",
                            key=_action_widget_key(action_id, "attack_bonus"),
                            placeholder="+7",
                        )
                        row[2].text_input(
                            "RW Attribut",
                            key=_action_widget_key(action_id, "save_ability"),
                            placeholder="Wei",
                        )
                        row[3].text_input(
                            "RW SG",
                            key=_action_widget_key(action_id, "save_dc"),
                            placeholder="15",
                        )
                        row = st.columns(3)
                        row[0].text_input(
                            "Reichweite",
                            key=_action_widget_key(action_id, "range_text"),
                            placeholder="5 ft. oder 18m Kegel",
                        )
                        row[1].text_input(
                            "Ziel",
                            key=_action_widget_key(action_id, "target_text"),
                            placeholder="ein Ziel",
                        )
                        row[2].text_input(
                            "Schaden",
                            key=_action_widget_key(action_id, "damage_text"),
                            placeholder="2W6 + 4 Stich + 1W6 Feuer",
                        )
                        st.text_area(
                            "Effekt",
                            key=_action_widget_key(action_id, "effect_text"),
                            height=80,
                        )
                        st.text_area(
                            "Notizen",
                            key=_action_widget_key(action_id, "notes"),
                            height=60,
                        )
                    st.button(
                        "Aktion entfernen",
                        key=f"monster_creator_remove_action_{action_id}",
                        on_click=_remove_action,
                        args=(index,),
                        use_container_width=True,
                    )

            actions = []
            for action in st.session_state.get("monster_creator_actions", []):
                action_id = int(action.get("id", 0))
                actions.append(
                    {
                        "id": action_id,
                        "name": st.session_state.get(
                            _action_widget_key(action_id, "name"), ""
                        ),
                        "linked_spell": st.session_state.get(
                            _action_widget_key(action_id, "linked_spell"), ""
                        ),
                        "action_type": st.session_state.get(
                            _action_widget_key(action_id, "action_type"), "standard"
                        ),
                        "category": st.session_state.get(
                            _action_widget_key(action_id, "category"), "melee"
                        ),
                        "usage_limit": st.session_state.get(
                            _action_widget_key(action_id, "usage_limit"), ""
                        ),
                        "attack_bonus": st.session_state.get(
                            _action_widget_key(action_id, "attack_bonus"), ""
                        ),
                        "save_ability": st.session_state.get(
                            _action_widget_key(action_id, "save_ability"), ""
                        ),
                        "save_dc": st.session_state.get(
                            _action_widget_key(action_id, "save_dc"), ""
                        ),
                        "range_text": st.session_state.get(
                            _action_widget_key(action_id, "range_text"), ""
                        ),
                        "target_text": st.session_state.get(
                            _action_widget_key(action_id, "target_text"), ""
                        ),
                        "damage_text": st.session_state.get(
                            _action_widget_key(action_id, "damage_text"), ""
                        ),
                        "effect_text": st.session_state.get(
                            _action_widget_key(action_id, "effect_text"), ""
                        ),
                        "notes": st.session_state.get(
                            _action_widget_key(action_id, "notes"), ""
                        ),
                    }
                )
            st.session_state["monster_creator_actions"] = actions

            st.checkbox(
                "Zauberwirken aktivieren",
                key="monster_creator_has_spellcasting",
                help="Blendet den Zauberblock fuer das Bestiarium ein.",
            )
            if st.session_state.get("monster_creator_has_spellcasting", False):
                row = st.columns(4)
                row[0].selectbox(
                    "Zauberattribut",
                    ["Intelligenz", "Weisheit", "Charisma"],
                    key="monster_creator_spellcasting_ability",
                )
                row[1].number_input(
                    "Zauber SG",
                    min_value=1,
                    max_value=30,
                    key="monster_creator_spell_dc",
                )
                row[2].number_input(
                    "Zauberangriff",
                    min_value=-10,
                    max_value=20,
                    key="monster_creator_spell_attack_bonus",
                )
                row[3].text_input(
                    "Zauberwirker-Text",
                    key="monster_creator_spellcaster_level",
                    placeholder="Zum Beispiel: Zauberwirker des 7. Grades",
                )
                st.text_input("Zauberplaetze", key="monster_creator_spell_slots")
                st.multiselect(
                    "Zaubertricks",
                    _spell_options_for_level(
                        0, st.session_state.get("monster_creator_cantrips", [])
                    ),
                    key="monster_creator_cantrips",
                )
                for level in range(1, 10):
                    st.multiselect(
                        f"Grad {level}",
                        _spell_options_for_level(
                            level,
                            st.session_state.get(
                                f"monster_creator_spells_level_{level}", []
                            ),
                        ),
                        key=f"monster_creator_spells_level_{level}",
                    )
                st.multiselect(
                    "Pro Tag",
                    _all_spell_options(
                        st.session_state.get("monster_creator_spells_per_day", [])
                    ),
                    key="monster_creator_spells_per_day",
                )
                st.text_area(
                    "Sonderzauber", key="monster_creator_special_spells", height=80
                )

            with st.expander("Encounter-Metadaten", expanded=False):
                st.checkbox(
                    "Katalog-Metadaten exportieren",
                    key="monster_creator_catalog_enabled",
                )
                if st.session_state.get("monster_creator_catalog_enabled", False):
                    st.text_input("Katalog-Key", key="monster_creator_catalog_key")
                    row = st.columns(2)
                    row[0].selectbox(
                        "Strategie-Override",
                        MONSTER_CATALOG_STRATEGIES,
                        key="monster_creator_strategy_override",
                    )
                    row[1].multiselect(
                        "Tags-Override",
                        MONSTER_CATALOG_TAG_OPTIONS,
                        key="monster_creator_tags_override",
                    )
                    row = st.columns(3)
                    row[0].number_input(
                        "Threat-Override",
                        key="monster_creator_threat_override",
                        format="%.2f",
                    )
                    row[1].number_input(
                        "Action-Override",
                        key="monster_creator_action_override",
                        format="%.2f",
                    )
                    row[2].number_input(
                        "Volatilitaet-Override",
                        key="monster_creator_volatility_override",
                        format="%.2f",
                    )
                    row = st.columns(4)
                    row[0].checkbox(
                        "Legendaere Aktionen",
                        key="monster_creator_legendary_actions_override",
                    )
                    row[1].checkbox(
                        "Legendaere Resistenzen",
                        key="monster_creator_legendary_resistances_override",
                    )
                    row[2].checkbox(
                        "Phasenwechsel",
                        key="monster_creator_phase_change_override",
                    )
                    row[3].checkbox(
                        "Beschwoerung",
                        key="monster_creator_summons_override",
                    )
                    st.text_area(
                        "Katalog-Hinweis",
                        key="monster_creator_catalog_hint",
                        height=80,
                    )

        with st.container(border=True):
            st.markdown("**Lore und Export**")
            st.text_area("Taktik", key="monster_creator_tactics", height=120)
            st.text_area("Ausruestung", key="monster_creator_equipment", height=100)
            st.text_area("Hintergrund", key="monster_creator_background", height=140)
            st.text_area("Zitate", key="monster_creator_quotes", height=80)
            st.text_area("Notizen", key="monster_creator_notes", height=80)
            if st.button(
                "Monster nach World/Bestiarium exportieren",
                use_container_width=True,
            ):
                export_success, export_message = _export_monster_markdown()
                if export_success:
                    st.success(f"Monster exportiert nach {export_message}")
                else:
                    st.warning(export_message)

    with preview_col:
        profile = _monster_profile_values()
        warnings = _validate_monster_profile(profile)
        with st.container(border=True):
            st.markdown("**Vorschau**")
            if warnings:
                for warning in warnings:
                    st.warning(warning)
            st.markdown(f"## {profile['name'] or 'Monstername'}")
            st.caption(
                f"CR {profile['cr'] or '-'} | {profile['type'] or '-'} | {profile['role'] or '-'}"
            )
            st.markdown(_render_export_markdown())
            with st.expander("Rohes Markdown", expanded=False):
                st.code(_render_export_markdown(), language="markdown")
