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
MONSTER_ACTION_CATEGORY_LABELS = {
    "melee": "Nahkampf",
    "ranged": "Fernkampf",
    "spell": "Zauber",
    "aura": "Aura",
    "control": "Kontrolle",
    "summon": "Beschwoerung",
    "utility": "Unterstuetzung",
}
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
MONSTER_LOADED_MONSTER_KEY = "monster_creator_loaded_monster"


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


def _monster_alignment_select_options() -> list[str]:
    current_value = st.session_state.get("monster_creator_alignment", "").strip()
    if current_value and current_value not in MONSTER_ALIGNMENT_OPTIONS:
        return [current_value, *MONSTER_ALIGNMENT_OPTIONS]
    return list(MONSTER_ALIGNMENT_OPTIONS)


def _action_category_label(category: str) -> str:
    return MONSTER_ACTION_CATEGORY_LABELS.get(category, category)


def _monster_export_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "World" / "Bestiarium"


def _monster_template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "World" / "templates" / "monster.md"


def _sanitize_filename(name: str) -> str:
    normalized = name.strip() or "Unbenanntes Monster"
    normalized = re.sub(r"[^A-Za-z0-9 _().-]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or "Unbenanntes Monster"


def _replace_template_line(content: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^(\s*-\s+\*\*{re.escape(label)}:\*\*).*?$", re.MULTILINE)
    replacement = rf"\1 {value}" if value else r"\1"
    return pattern.sub(replacement, content, count=1)


def _replace_template_section(content: str, heading: str, section_body: str) -> str:
    pattern = re.compile(
        rf"(^##\s+{re.escape(heading)}\s*$)(.*?)(?=^---\s*$|^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    def replace(match):
        return f"{match.group(1)}\n\n{section_body.strip()}\n\n"

    return pattern.sub(replace, content, count=1)


def _insert_catalog_section(content: str, catalog_section: str) -> str:
    if not catalog_section.strip():
        return content
    return content.replace("---", f"{catalog_section.strip()}\n\n---", 1)


def _set_first_heading(content: str, title: str) -> str:
    return re.sub(r"^#\s+.+$", f"# {title}", content, count=1, flags=re.MULTILINE)


def _all_bestiary_monster_names() -> list[str]:
    export_dir = _monster_export_directory()
    if not export_dir.exists():
        return []
    return sorted((path.stem for path in export_dir.glob("*.md")), key=str.casefold)


def _bestiary_monster_file(monster_name: str) -> Path:
    exact_match = _monster_export_directory() / f"{monster_name}.md"
    if exact_match.exists():
        return exact_match

    normalized_name = monster_name.casefold()
    for path in _monster_export_directory().glob("*.md"):
        if path.stem.casefold() == normalized_name:
            return path
    raise FileNotFoundError(f"Monster nicht gefunden: {monster_name}")


def _extract_template_line_value(content: str, label: str) -> str:
    normalized_label = re.sub(r"\s+", " ", label).strip().casefold()
    for raw_line in content.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line.startswith("- **"):
            continue
        match = re.match(r"^-\s+\*\*(.+?):\*\*([ \t]*.*)$", stripped_line)
        if match is None:
            continue
        current_label = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
        if current_label != normalized_label:
            continue
        return match.group(2).strip()
    return ""


def _extract_section_content(content: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n?(.*?)(?=^---\s*$|^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def _parse_stat_cell(value: str) -> int:
    match = re.search(r"-?\d+", value)
    return int(match.group()) if match else 10


def _parse_bonus_cell(value: str) -> str:
    cleaned = value.strip()
    return "" if cleaned == "-" else cleaned


def _parse_csv_value(value: str) -> list[str]:
    cleaned = value.strip()
    if not cleaned or cleaned == "-":
        return []
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _parse_movement(value: str) -> dict[str, int]:
    movement = {"walk": 0, "fly": 0, "swim": 0, "climb": 0, "burrow": 0}
    for part in [item.strip() for item in value.split(",") if item.strip()]:
        number_match = re.search(r"(\d+)", part)
        if not number_match:
            continue
        distance = int(number_match.group(1))
        lowered = part.casefold()
        if "flug" in lowered:
            movement["fly"] = distance
        elif "schwimmen" in lowered:
            movement["swim"] = distance
        elif "klettern" in lowered:
            movement["climb"] = distance
        elif "graben" in lowered:
            movement["burrow"] = distance
        else:
            movement["walk"] = distance
    return movement


def _parse_table_rows(content: str) -> tuple[dict[str, int], dict[str, str]]:
    stats = {key: 10 for key, _ in MONSTER_STAT_FIELDS}
    saves = {key: "" for key, _ in MONSTER_STAT_FIELDS}
    attribute_match = re.search(
        r"^\|\s*Attribut(?:e)?\s*\|(.*?)\|$", content, re.MULTILINE
    )
    save_match = re.search(r"^\|\s*Rettung(?:s\.)?\s*\|(.*?)\|$", content, re.MULTILINE)
    if attribute_match:
        cells = [cell.strip() for cell in attribute_match.group(1).split("|")]
        for (key, _label), cell in zip(MONSTER_STAT_FIELDS, cells):
            stats[key] = _parse_stat_cell(cell)
    if save_match:
        cells = [cell.strip() for cell in save_match.group(1).split("|")]
        for (key, _label), cell in zip(MONSTER_STAT_FIELDS, cells):
            saves[key] = _parse_bonus_cell(cell)
    return (stats, saves)


def _parse_spell_list_block(block: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"\[\[([^\]]+)\]\]", block)]


def _parse_inline_action_details(detail_text: str) -> dict[str, str]:
    parsed = {
        "attack_bonus": "",
        "range_text": "",
        "damage_text": "",
        "effect_text": "",
    }
    remaining_parts: list[str] = []

    for raw_part in [part.strip() for part in detail_text.split(",") if part.strip()]:
        part = raw_part

        attack_match = re.match(
            r"^([+-]?\d+)\s+zum Treffen\b(.*)$", part, re.IGNORECASE
        )
        if attack_match:
            parsed["attack_bonus"] = attack_match.group(1).strip()
            trailing = attack_match.group(2).strip()
            if trailing:
                remaining_parts.append(trailing)
            continue

        range_match = re.match(
            r"^(?:Reichweite\s+)?(\d+(?:[.,]\d+)?m(?:\s+bis\s+\d+(?:[.,]\d+)?m)?)(?:\s+Reichweite)?\b(.*)$",
            part,
            re.IGNORECASE,
        )
        if range_match:
            parsed["range_text"] = range_match.group(1).strip()
            trailing = range_match.group(2).strip(" ,")
            if trailing:
                remaining_parts.append(trailing)
            continue

        remaining_parts.append(part)

    unresolved_parts: list[str] = []
    for part in remaining_parts:
        if not parsed["damage_text"] and re.search(r"\d+W\d+", part, re.IGNORECASE):
            parsed["damage_text"] = part.strip()
            continue
        unresolved_parts.append(part)

    parsed["effect_text"] = ", ".join(unresolved_parts).strip()
    return parsed


def _extract_save_details(detail_text: str) -> tuple[str, str, str]:
    match = re.search(
        r"\b(?:(ein(?:e|en|em|er)?)\s+)?(St(?:ä|ae)?rke|Str|Ges(?:chick)?|Dex(?:terity)?|Kon(?:sti(?:tution)?|s?it)?|Con(?:stitution)?|Int(?:elligenz)?|Wei(?:sheit)?|Wis(?:dom)?|Cha(?:risma)?)\s+Rettungswurf\s+SG\s*(\d+)\b",
        detail_text,
        re.IGNORECASE,
    )
    if match is None:
        return ("", "", detail_text.strip())

    ability_map = {
        "stärke": "Stärke",
        "staerke": "Stärke",
        "str": "Stärke",
        "geschick": "Geschick",
        "ges": "Geschick",
        "dexterity": "Geschick",
        "dex": "Geschick",
        "konsti": "Konstitution",
        "konsit": "Konstitution",
        "kon": "Konstitution",
        "con": "Konstitution",
        "konstitution": "Konstitution",
        "constitution": "Konstitution",
        "int": "Intelligenz",
        "intelligenz": "Intelligenz",
        "weisheit": "Weisheit",
        "wei": "Weisheit",
        "wisdom": "Weisheit",
        "wis": "Weisheit",
        "charisma": "Charisma",
        "cha": "Charisma",
    }
    article = (match.group(1) or "").strip()
    normalized = match.group(2).casefold()
    save_ability = ability_map.get(normalized, match.group(2).strip())
    save_dc = match.group(3).strip()
    replacement = f"{article} Rettungswurf".strip()
    cleaned_text = re.sub(
        r"\s{2,}",
        " ",
        f"{detail_text[:match.start()]} {replacement} {detail_text[match.end():]}",
    ).strip(" .,;")
    return (save_ability, save_dc, cleaned_text)


def _resolve_action_type_hint(value: str) -> str:
    normalized = value.strip().casefold()
    action_type_map = {
        "reaktion": "reaction",
        "reaktions": "reaction",
        "bonusaktion": "bonus",
        "bonus action": "bonus",
        "legendenaktion": "legendary",
        "legendary": "legendary",
        "passiv": "passive",
        "passive": "passive",
        "spezialfähigkeit": "special",
        "spezialfaehigkeit": "special",
    }
    return action_type_map.get(normalized, "")


def _parse_spellcasting_state(action_block: str) -> dict[str, object]:
    result: dict[str, object] = {
        "has_spellcasting": False,
        "spellcaster_level": "",
        "spell_slots": "",
        "cantrips": [],
        "spells_by_level": {level: [] for level in range(1, 10)},
        "spells_per_day": [],
        "special_spells": "",
    }
    spell_section_match = re.search(
        r"### Zauber\n(.*?)(?=^###\s+|\Z)", action_block, re.MULTILINE | re.DOTALL
    )
    if not spell_section_match:
        return result
    result["has_spellcasting"] = True
    spell_section = spell_section_match.group(1).strip()
    first_line = next(
        (line.strip() for line in spell_section.splitlines() if line.strip()), ""
    )
    result["spellcaster_level"] = first_line
    slot_match = re.search(
        r"\*\*Zauberpl[aä]tze:\*\*\s*(.*)$", spell_section, re.MULTILINE
    )
    if slot_match:
        result["spell_slots"] = slot_match.group(1).strip().replace("-", "").strip()
    cantrip_match = re.search(
        r"\*\*Zaubertricks:\*\*(.*?)(?=\*\*\d+\. Grad:\*\*|\*\*Pro Tag:\*\*|\*\*Sonderzauber:\*\*|\Z)",
        spell_section,
        re.MULTILINE | re.DOTALL,
    )
    if cantrip_match:
        result["cantrips"] = _parse_spell_list_block(cantrip_match.group(1))
    for level in range(1, 10):
        level_match = re.search(
            rf"\*\*{level}\. Grad:\*\*(.*?)(?=\*\*\d+\. Grad:\*\*|\*\*Pro Tag:\*\*|\*\*Sonderzauber:\*\*|\Z)",
            spell_section,
            re.MULTILINE | re.DOTALL,
        )
        if level_match:
            result["spells_by_level"][level] = _parse_spell_list_block(
                level_match.group(1)
            )
    per_day_match = re.search(
        r"\*\*Pro Tag:\*\*(.*?)(?=\*\*Sonderzauber:\*\*|\Z)",
        spell_section,
        re.MULTILINE | re.DOTALL,
    )
    if per_day_match:
        result["spells_per_day"] = _parse_spell_list_block(per_day_match.group(1))
    special_match = re.search(
        r"\*\*Sonderzauber:\*\*(.*)$", spell_section, re.MULTILINE | re.DOTALL
    )
    if special_match:
        result["special_spells"] = special_match.group(1).strip()
    return result


def _parse_actions_state(action_block: str) -> list[dict[str, str | int]]:
    section_map = {
        "Standard": "standard",
        "Spezialfähigkeiten": "special",
        "Spezialfaehigkeiten": "special",
        "Bonusaktionen": "bonus",
        "Reaktionen": "reaction",
        "Legendenaktionen": "legendary",
        "Passive Faehigkeiten": "passive",
    }
    actions: list[dict[str, str | int]] = []
    current_type = "standard"
    current_action: dict[str, str | int] | None = None
    for raw_line in action_block.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            heading = stripped[4:].strip()
            current_type = section_map.get(heading, current_type)
            current_action = None
            continue
        action_match = re.match(r"^-\s+\*\*(.+?)\*\*\s*(.*)$", stripped)
        if action_match:
            action_name = action_match.group(1).rstrip(":").strip()
            inline_detail = action_match.group(2).strip()
            usage_limit = ""
            usage_match = re.match(r"^(.*?)\s+\(([^)]+)\)$", action_name)
            if usage_match:
                action_name = usage_match.group(1).strip()
                bracket_value = usage_match.group(2).strip()
                hinted_action_type = _resolve_action_type_hint(bracket_value)
                if hinted_action_type:
                    current_type = hinted_action_type
                else:
                    usage_limit = bracket_value
            current_action = _empty_monster_action()
            current_action["action_type"] = current_type
            current_action["name"] = action_name
            current_action["usage_limit"] = usage_limit
            if inline_detail.startswith(":"):
                inline_detail = inline_detail[1:].strip()
            if inline_detail:
                inline_parts = _parse_inline_action_details(inline_detail)
                current_action["attack_bonus"] = inline_parts["attack_bonus"]
                current_action["range_text"] = inline_parts["range_text"]
                current_action["damage_text"] = inline_parts["damage_text"]
                save_ability, save_dc, cleaned_effect = _extract_save_details(
                    inline_parts["effect_text"]
                )
                current_action["save_ability"] = save_ability
                current_action["save_dc"] = save_dc
                current_action["effect_text"] = (
                    cleaned_effect.removeprefix("Reichweite. ")
                    .removeprefix("Sichweite. ")
                    .strip()
                )
            actions.append(current_action)
            continue
        if (
            stripped.startswith("- ") or stripped.startswith("* ")
        ) and current_action is not None:
            detail = stripped[2:].strip()
            if detail.startswith("Zauber: "):
                current_action["linked_spell"] = re.sub(
                    r"^[\[]\[|\][\]]$", "", detail.replace("Zauber:", "", 1).strip()
                )
            elif detail.startswith("Angriff: "):
                current_action["attack_bonus"] = (
                    detail.replace("Angriff:", "", 1).split(" ")[0].strip()
                )
            elif detail.startswith("Rettungswurf: "):
                save_text = detail.replace("Rettungswurf:", "", 1).strip()
                parts = save_text.split(" SG ")
                if len(parts) == 2:
                    current_action["save_ability"] = parts[0].strip()
                    current_action["save_dc"] = parts[1].strip()
            elif detail.startswith("Reichweite: "):
                current_action["range_text"] = detail.replace(
                    "Reichweite:", "", 1
                ).strip()
            elif detail.startswith("Ziel: "):
                current_action["target_text"] = detail.replace("Ziel:", "", 1).strip()
            elif detail.startswith("Schaden: "):
                current_action["damage_text"] = detail.replace(
                    "Schaden:", "", 1
                ).strip()
            else:
                inline_parts = _parse_inline_action_details(detail)
                field_was_already_present = any(
                    (
                        inline_parts["attack_bonus"]
                        and current_action.get("attack_bonus"),
                        inline_parts["range_text"] and current_action.get("range_text"),
                        inline_parts["damage_text"]
                        and current_action.get("damage_text"),
                    )
                )
                if inline_parts["attack_bonus"] and not current_action.get(
                    "attack_bonus"
                ):
                    current_action["attack_bonus"] = inline_parts["attack_bonus"]
                if inline_parts["range_text"] and not current_action.get("range_text"):
                    current_action["range_text"] = inline_parts["range_text"]
                if inline_parts["damage_text"] and not current_action.get(
                    "damage_text"
                ):
                    current_action["damage_text"] = inline_parts["damage_text"]

                save_ability, save_dc, remaining_text = _extract_save_details(
                    inline_parts["effect_text"]
                )
                if save_ability and not current_action.get("save_ability"):
                    current_action["save_ability"] = save_ability
                if save_dc and not current_action.get("save_dc"):
                    current_action["save_dc"] = save_dc
                remaining_text = (
                    remaining_text.removeprefix("Reichweite. ")
                    .removeprefix("Sichweite. ")
                    .strip()
                )
                if remaining_text and not current_action.get("effect_text"):
                    current_action["effect_text"] = remaining_text
                elif remaining_text:
                    notes = str(current_action.get("notes", "")).strip()
                    current_action["notes"] = f"{notes}\n{remaining_text}".strip()
                elif field_was_already_present:
                    notes = str(current_action.get("notes", "")).strip()
                    current_action["notes"] = f"{notes}\n{detail}".strip()
    return actions or [_empty_monster_action()]


def _load_monster_into_state(monster_name: str) -> None:
    content = _bestiary_monster_file(monster_name).read_text(encoding="utf-8")
    stats, saves = _parse_table_rows(content)
    action_block = _extract_section_content(content, "Aktionen")
    spell_state = _parse_spellcasting_state(action_block)
    movement = _parse_movement(_extract_template_line_value(content, "Bewegung"))

    st.session_state["monster_creator_name"] = re.sub(
        r"^#\s+", "", content.splitlines()[0]
    ).strip()
    st.session_state["monster_creator_foundation"] = (
        _extract_template_line_value(content, "Grundlage")
        or MONSTER_FOUNDATION_OPTIONS[0]
    )
    st.session_state["monster_creator_cr"] = _extract_template_line_value(
        content, "Stufe/Herausfordungsgrad"
    )
    st.session_state["monster_creator_alias"] = (
        _extract_template_line_value(content, "Alias").replace("-", "").strip()
    )
    st.session_state["monster_creator_age"] = (
        _extract_template_line_value(content, "Alter").replace("-", "").strip()
        or MONSTER_UNKNOWN_VALUE
    )
    st.session_state["monster_creator_languages"] = (
        _extract_template_line_value(content, "Sprachen").replace("-", "").strip()
    )
    st.session_state["monster_creator_traits"] = (
        _extract_template_line_value(content, "Merkmale").replace("-", "").strip()
    )
    st.session_state["monster_creator_type"] = "Frei eingeben"
    st.session_state["monster_creator_type_custom"] = (
        _extract_template_line_value(content, "Volk").replace("-", "").strip()
    )
    st.session_state["monster_creator_origin"] = "Frei eingeben"
    st.session_state["monster_creator_origin_custom"] = (
        _extract_template_line_value(content, "Herkunft").replace("-", "").strip()
    )
    st.session_state["monster_creator_role"] = "Frei eingeben"
    st.session_state["monster_creator_role_custom"] = (
        _extract_template_line_value(content, "Klasse").replace("-", "").strip()
    )
    alignment_value = (
        _extract_template_line_value(content, "Gesinnung").replace("-", "").strip()
    )
    st.session_state["monster_creator_alignment"] = alignment_value or "Neutral"
    st.session_state["monster_creator_alignment_custom"] = ""

    armor_line = _extract_template_line_value(content, "Rüstungsklasse (RK)/Rüstung")
    armor_match = re.match(r"(\d+)(.*)$", armor_line)
    if armor_match:
        st.session_state["monster_creator_ac"] = int(armor_match.group(1))
        st.session_state["monster_creator_armor_text"] = armor_match.group(2).strip()
    st.session_state["monster_creator_weapons"] = (
        _extract_template_line_value(content, "Waffen").replace("-", "").strip()
    )
    initiative_text = _extract_template_line_value(content, "Initiative")
    st.session_state["monster_creator_initiative"] = (
        int(re.search(r"-?\d+", initiative_text).group())
        if re.search(r"-?\d+", initiative_text)
        else 0
    )
    hp_text = _extract_template_line_value(content, "Trefferpunkte")
    st.session_state["monster_creator_hp"] = (
        int(re.search(r"\d+", hp_text).group()) if re.search(r"\d+", hp_text) else 1
    )
    st.session_state["monster_creator_hit_dice"] = (
        _extract_template_line_value(content, "Trefferwürfel").replace("-", "").strip()
    )
    perception_text = _extract_template_line_value(content, "Passive Wahrnehmung")
    st.session_state["monster_creator_passive_perception"] = (
        int(re.search(r"\d+", perception_text).group())
        if re.search(r"\d+", perception_text)
        else 10
    )
    st.session_state["monster_creator_skill_lines"] = (
        _extract_template_line_value(content, "Fertigkeiten").replace("-", "").strip()
    )
    st.session_state["monster_creator_immunities"] = _parse_csv_value(
        _extract_template_line_value(content, "Immunitäten")
    )
    st.session_state["monster_creator_resistances"] = _parse_csv_value(
        _extract_template_line_value(content, "Resistenzen")
    )
    st.session_state["monster_creator_weaknesses"] = _parse_csv_value(
        _extract_template_line_value(content, "Schwächen")
    )

    for key, _label in MONSTER_STAT_FIELDS:
        st.session_state[f"monster_creator_{key}"] = stats[key]
        st.session_state[f"monster_creator_save_{key}"] = saves[key]

    for movement_key, state_key in (
        ("walk", "monster_creator_move_walk"),
        ("fly", "monster_creator_move_fly"),
        ("swim", "monster_creator_move_swim"),
        ("climb", "monster_creator_move_climb"),
        ("burrow", "monster_creator_move_burrow"),
    ):
        st.session_state[state_key] = movement[movement_key]

    st.session_state["monster_creator_tactics"] = (
        _extract_section_content(content, "Taktik").replace("-", "").strip()
    )
    st.session_state["monster_creator_equipment"] = (
        _extract_section_content(content, "Ausrüstung").replace("-", "").strip()
    )
    st.session_state["monster_creator_background"] = (
        _extract_section_content(content, "Hintergrund").replace("-", "").strip()
    )
    st.session_state["monster_creator_quotes"] = (
        _extract_section_content(content, "Zitate").replace("-", "").strip()
    )
    st.session_state["monster_creator_notes"] = _extract_section_content(
        content, "Notizen"
    )
    st.session_state[MONSTER_LOADED_MONSTER_KEY] = monster_name

    st.session_state["monster_creator_has_spellcasting"] = bool(
        spell_state["has_spellcasting"]
    )
    st.session_state["monster_creator_spellcaster_level"] = str(
        spell_state["spellcaster_level"]
    )
    st.session_state["monster_creator_spell_slots"] = str(spell_state["spell_slots"])
    st.session_state["monster_creator_cantrips"] = list(spell_state["cantrips"])
    for level in range(1, 10):
        st.session_state[f"monster_creator_spells_level_{level}"] = list(
            spell_state["spells_by_level"][level]
        )
    st.session_state["monster_creator_spells_per_day"] = list(
        spell_state["spells_per_day"]
    )
    st.session_state["monster_creator_special_spells"] = str(
        spell_state["special_spells"]
    )
    st.session_state["monster_creator_actions"] = _parse_actions_state(action_block)


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
        MONSTER_LOADED_MONSTER_KEY: "",
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
        "monster_creator_alignment": "Neutral",
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


def _reset_monster_creator_form(*, preserve_existing_selection: bool = False) -> None:
    preserved_state: dict[str, object] = {}
    if preserve_existing_selection and "monster_creator_existing_monster" in st.session_state:
        preserved_state["monster_creator_existing_monster"] = st.session_state[
            "monster_creator_existing_monster"
        ]

    for key in list(st.session_state.keys()):
        if key.startswith("monster_creator_"):
            del st.session_state[key]

    st.session_state.update(preserved_state)
    _ensure_monster_creator_state()


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
        "alignment": st.session_state.get("monster_creator_alignment", "").strip(),
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

    template = _monster_template_path().read_text(encoding="utf-8")
    template = _set_first_heading(template, name)
    template = _replace_template_line(template, "Grundlage", str(profile["foundation"]))
    template = _replace_template_line(
        template, "Stufe/Herausfordungsgrad", _text_or_dash(str(profile["cr"]))
    )
    template = _replace_template_line(
        template, "Volk", _text_or_dash(str(profile["type"]))
    )
    template = _replace_template_line(
        template, "Herkunft", _text_or_dash(str(profile["origin"]))
    )
    template = _replace_template_line(
        template, "Klasse", _text_or_dash(str(profile["role"]))
    )
    template = _replace_template_line(
        template, "Alias", _text_or_dash(str(profile["alias"]))
    )
    template = _replace_template_line(
        template, "Alter", _text_or_dash(str(profile["age"]))
    )
    template = _replace_template_line(
        template, "Gesinnung", _text_or_dash(str(profile["alignment"]))
    )
    template = _replace_template_line(
        template, "Sprachen", _text_or_dash(str(profile["languages"]))
    )
    template = _replace_template_line(
        template, "Merkmale", _text_or_dash(str(profile["traits"]))
    )

    properties_block = "\n".join(
        [
            f"- **Rüstungsklasse (RK)/Rüstung:** {profile['ac']} {str(profile['armor_text']).strip()}".rstrip(),
            f"- **Waffen:** {_text_or_dash(str(profile['weapons']))}",
            f"- **Initiative:** {profile['initiative']:+d}",
            f"- **Bewegung:** {movement_text}",
            f"- **Trefferpunkte:** {profile['hp']}",
            f"- **Trefferwürfel:** {_text_or_dash(str(profile['hit_dice']))}",
            f"- **Passive Wahrnehmung:** {profile['passive_perception']}",
            f"- **Fertigkeiten:** {_multiline_or_dash(str(profile['skills']))}",
            "",
            table_header,
            table_rule,
            attribute_row,
            save_row,
            "",
            f"- **Immunitäten:** {_format_selected_values(profile['immunities'])}",
            f"- **Resistenzen:** {_format_selected_values(profile['resistances'])}",
            f"- **Schwächen:** {_format_selected_values(profile['weaknesses'])}",
        ]
    )
    action_block = (
        "\n\n".join(action_sections)
        if action_sections
        else "### Standard\n\n- **Mehrfachangriff:**"
    )

    template = _insert_catalog_section(template, catalog_section)
    template = _replace_template_section(template, "Eigenschaften", properties_block)
    template = _replace_template_section(template, "Aktionen", action_block)
    template = _replace_template_section(
        template, "Taktik", _multiline_or_dash(str(profile["tactics"]))
    )
    template = _replace_template_section(
        template, "Ausrüstung", _multiline_or_dash(str(profile["equipment"]))
    )
    template = _replace_template_section(
        template, "Hintergrund", _multiline_or_dash(str(profile["background"]))
    )
    template = _replace_template_section(
        template, "Zitate", _multiline_or_dash(str(profile["quotes"]))
    )

    if profile["notes"]:
        template = (
            template.rstrip()
            + f"\n\n---\n\n## Notizen\n\n{str(profile['notes']).strip()}\n"
        )

    return template.strip() + "\n"


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


def _export_monster_markdown(
    *,
    overwrite: bool = False,
    target_name: str | None = None,
) -> tuple[bool, str]:
    export_dir = _monster_export_directory()
    export_dir.mkdir(parents=True, exist_ok=True)
    resolved_name = target_name or st.session_state.get("monster_creator_name", "")
    file_name = f"{_sanitize_filename(str(resolved_name))}.md"
    export_path = export_dir / file_name
    if export_path.exists() and not overwrite:
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


def render_monster_creator_view() -> None:
    if not monster_creator_is_admin():
        st.warning("Der Monster-Ersteller ist nur fuer Spielleiter verfuegbar.")
        return

    _ensure_monster_creator_state()
    bestiary_monsters = _all_bestiary_monster_names()

    st.subheader("Monster Ersteller")
    st.caption(
        "Erfasst Kernwerte, Aktionen und Export fuer Bestiarium-Eintraege auf Basis des Monster-Templates."
    )

    with st.container(border=True):
        control_col, reset_col, overwrite_col = st.columns(
            (4, 1, 1), vertical_alignment="bottom"
        )
        with control_col:
            selected_existing_monster = st.selectbox(
                "Bestehendes Bestiarium-Monster bearbeiten",
                [""] + bestiary_monsters,
                key="monster_creator_existing_monster",
                format_func=lambda value: value or "Neues Monster erstellen",
            )
            st.caption("Die Auswahl wird direkt in den Editor geladen.")

        loaded_monster = str(st.session_state.get(MONSTER_LOADED_MONSTER_KEY, ""))
        if selected_existing_monster and selected_existing_monster != loaded_monster:
            _load_monster_into_state(selected_existing_monster)
        elif not selected_existing_monster and loaded_monster:
            _reset_monster_creator_form(preserve_existing_selection=True)

        if reset_col.button("Leeren", use_container_width=True):
            _reset_monster_creator_form()
            st.rerun()
        overwrite_requested = overwrite_col.button(
            "Ueberschreiben",
            use_container_width=True,
            disabled=not selected_existing_monster,
            help="Speichert die aktuelle Formularansicht in die ausgewaehlte Bestiarium-Datei.",
        )

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
                _monster_alignment_select_options(),
                key="monster_creator_alignment",
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
                        format_func=_action_category_label,
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
                "Monster nach World/Bestiarium exportieren", use_container_width=True
            ):
                export_success, export_message = _export_monster_markdown()
                if export_success:
                    st.success(f"Monster exportiert nach {export_message}")
                else:
                    st.warning(export_message)
            if overwrite_requested:
                export_success, export_message = _export_monster_markdown(
                    overwrite=True,
                    target_name=selected_existing_monster,
                )
                if export_success:
                    st.success(f"Monster aktualisiert: {export_message}")
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


def monster_creator_view() -> None:
    set_to_monster_creator_view()
    render_monster_creator_view()
