from __future__ import annotations

from datetime import date
from pathlib import Path
import re

import streamlit as st

from wiki_dasboard.components.metadata import (
    build_time_metadata,
    metadata_display_rows,
    normalize_metadata_links,
    normalize_metadata_regions,
    normalize_metadata_tags,
    serialize_frontmatter,
    split_frontmatter,
)
from wiki_dasboard.config import cfg


ENTRY_CONFIGS = {
    "Trank": {
        "type": "Trank",
        "collection": "Tranksammlung",
        "template": "trank_template.md",
        "frontmatter": {
            "seltenheit": "rarity",
            "wert": "value",
            "komponenten": "components",
        },
        "fields": (
            ("components", "Komponenten", "text", "Mohnblüte, Trollharz"),
            ("craft", "Herstellung", "text", "8 Stunden köcheln und filtern"),
            ("value", "Wert", "text", "50G"),
            ("check", "Probe", "text", "INT oder WIS + Alchemistenwerkzeug"),
            ("dc", "SG", "text", "10"),
            ("success", "Erfolg", "area", "Wirkung bei gelungener Herstellung"),
            ("weakened", "Geschwächt", "area", "Wirkung bei knappem Fehlschlag"),
            ("rarity", "Seltenheit", "text", "Gewöhnlich"),
        ),
        "body_fields": {
            "tag": ("Tag", "plain"),
            "components": ("Komponenten", "bold"),
            "craft": ("Herstellung", "bold"),
            "value": ("Wert", "bold"),
            "check": ("Probe", "bold"),
            "dc": ("SG", "bold"),
            "success": ("Erfolg", "bold"),
            "weakened": ("Geschwächt (SG um ≤5 verfehlt)", "bold"),
        },
    },
    "Zauber": {
        "type": "Zauber",
        "collection": "Zauberarchiv",
        "template": "spell_template.md",
        "frontmatter": {
            "grad": "level",
            "schule": "school",
            "konzentration": "concentration",
            "komponenten": "components",
            "materialien": "materials",
        },
        "fields": (
            ("level", "Grad", "text", "3"),
            ("school", "Schule", "text", "#Hervorrufung"),
            ("ritual", "Ritual", "text", "Nein"),
            ("concentration", "Konzentration", "text", "Nein"),
            ("casting", "Zauberzeit / Ausführung", "text", "1 Aktion"),
            ("range", "Reichweite", "text", "45 m"),
            ("components", "Komponenten", "text", "#Verbal #Geste #Material"),
            ("materials", "Materialien", "text", "Fledermausguano und Schwefel"),
            ("duration", "Dauer / Wirkung", "text", "sofort"),
            ("saves", "Rettungswürfe", "text", "Geschicklichkeit"),
            ("attack", "Angriffsart", "text", "Fernkampf"),
            ("damage", "Schaden / Heilung", "text", "8W6 Feuer"),
            ("conditions", "Zustände", "text", ""),
            ("description", "Beschreibung", "area", "Wirkung und Ablauf des Zaubers"),
        ),
        "body_fields": {
            "level": ("Grad", "bold"),
            "school": ("Schule", "bold"),
            "ritual": ("Ritual", "bold"),
            "concentration": ("Konzentration", "bold"),
            "casting": ("Zauberzeit/Ausführung", "bold"),
            "range": ("Reichweite", "bold"),
            "components": ("Komponenten", "bold"),
            "materials": ("Materialien", "bold"),
            "duration": ("Dauer/Wirkung", "bold"),
            "saves": ("Rettungswürfe", "bold"),
            "attack": ("Angriffsart", "bold"),
            "damage": ("Schaden/Heilung", "bold"),
            "conditions": ("Zustände", "bold"),
        },
        "sections": {"description": "Beschreibung"},
    },
    "Zutat": {
        "type": "Zutat",
        "collection": "Zutatenarchiv",
        "template": "zutaten_template.md",
        "frontmatter": {
            "seltenheit": "rarity",
            "wert": "value",
            "fundort": "location",
        },
        "fields": (
            ("rarity", "Seltenheit", "text", "#Gewöhnlich"),
            ("value", "Wert", "text", "6G"),
            ("location", "Fundort", "text", "Tiefe Wälder, Hexengärten"),
            ("description", "Beschreibung", "area", "Merkmale und Verwendung"),
        ),
        "body_fields": {
            "rarity": ("Seltenheit", "bold"),
            "value": ("Wert", "bold"),
            "location": ("Fundort", "bold"),
        },
        "sections": {"description": "Beschreibung"},
    },
    "Waffe": {
        "type": "Waffe",
        "collection": "Waffenkammer",
        "template": "waffen_template.md",
        "frontmatter": {
            "Waffentyp": "weapon_type",
            "Schadensart": "damage_type",
            "Kategorie": "category",
            "Wert": "value",
            "Einstimmung": "attunement",
            "seltenheit": "rarity",
            "reichweite": "range",
        },
        "fields": (
            ("weapon_type", "Waffentyp", "text", "Nahkampf"),
            ("category", "Kategorie", "text", "Streithammer"),
            ("rarity", "Seltenheit", "text", "Gewöhnlich"),
            ("damage", "Schaden", "text", "1W8 Wucht"),
            ("damage_type", "Schadensart", "text", "Wucht"),
            ("range", "Reichweite", "text", ""),
            ("value", "Wert", "text", ""),
            ("weight", "Gewicht", "text", ""),
            ("attunement", "Einstimmung", "bool", "Nein"),
            ("prerequisite", "Voraussetzung", "text", ""),
            ("location", "Fundort", "text", ""),
            ("description", "Beschreibung", "area", "Aussehen und Hintergrund"),
            ("mechanics", "Spielmechanik", "area", "Besondere Eigenschaften"),
        ),
        "body_fields": {
            "weapon_type": ("Waffentyp", "bold"),
            "category": ("Kategorie", "bold"),
            "rarity": ("Seltenheit", "bold"),
            "damage": ("Schaden", "bold"),
            "damage_type": ("Schadensart", "bold"),
            "range": ("Reichweite", "bold"),
            "value": ("Wert", "bold"),
            "weight": ("Gewicht", "bold"),
            "attunement": ("Einstimmung", "bold"),
            "prerequisite": ("Voraussetzung", "bold"),
            "location": ("Fundort", "bold"),
        },
        "sections": {"description": "Beschreibung", "mechanics": "Spielmechanik"},
        "visibility": "DM",
    },
    "Schatzkammer-Eintrag": {
        "type": "Artefakt",
        "collection": "Schatzkammer",
        "template": "schatzkammer_template.md",
        "frontmatter": {
            "seltenheit": "rarity",
            "einstimmung": "attunement",
            "kategorie": "category",
            "wert": "value",
        },
        "fields": (
            ("rarity", "Seltenheit", "text", ""),
            ("attunement", "Einstimmung", "text", ""),
            ("category", "Kategorie", "text", "Artefakt"),
            ("value", "Wert", "text", ""),
            ("prerequisite", "Voraussetzung", "text", ""),
            ("charges", "Ladungen", "text", ""),
            ("recharge", "Aufladung", "text", ""),
            ("location", "Fundort", "text", ""),
            ("description", "Beschreibung", "area", "Herkunft und Erscheinung"),
            ("mechanics", "Spielmechanik", "area", "Wirkung und Eigenschaften"),
        ),
        "body_fields": {
            "prerequisite": ("Voraussetzung", "bold"),
            "charges": ("Ladungen", "bold"),
            "recharge": ("Aufladung", "bold"),
            "location": ("Fundort", "bold"),
        },
        "sections": {"description": "Beschreibung", "mechanics": "Speilmechanik"},
        "visibility": "DM",
    },
}

COMMON_METADATA_FIELDS = (
    ("status", "Status", "vorbereitet"),
    ("campaigns", "Kampagne(n)", ""),
    ("regions", "Region(en)", ""),
    ("tags", "Tags", ""),
    ("time_text", "Zeitangabe", ""),
    ("start_year", "Jahr von", ""),
    ("end_year", "Jahr bis", ""),
)


def _state_key(entry_kind: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", entry_kind.lower()).strip("_")
    return f"entry_creator_{slug}_{name}"


def _ensure_entry_state(entry_kind: str) -> None:
    config = ENTRY_CONFIGS[entry_kind]
    defaults = {
        "name": "",
        "destination": "Sammlung",
        "status": "vorbereitet",
        "campaigns": "",
        "regions": "",
        "tags": "",
        "time_text": "",
        "start_year": "",
        "end_year": "",
    }
    defaults.update({key: "" for key in config["frontmatter"].values()})
    defaults.update(
        {
            field[0]: field[3] if field[2] == "bool" else ""
            for field in config["fields"]
        }
    )
    for name, value in defaults.items():
        key = _state_key(entry_kind, name)
        if key not in st.session_state:
            st.session_state[key] = value


def _entry_metadata(entry_kind: str) -> dict[str, object]:
    config = ENTRY_CONFIGS[entry_kind]

    def get(key: str) -> object:
        return st.session_state.get(_state_key(entry_kind, key), "")

    metadata: dict[str, object] = {
        "typ": config["type"],
        "status": get("status") or "vorbereitet",
        "kampagne": normalize_metadata_links(get("campaigns")),
        "region": normalize_metadata_regions(get("regions")),
        "tags": normalize_metadata_tags(get("tags")),
        **build_time_metadata(get("time_text"), get("start_year"), get("end_year")),
        "erstellt": date.today().isoformat(),
        "geaendert": date.today().isoformat(),
    }
    if "visibility" in config:
        metadata["sichtbarkeit"] = config["visibility"]
    for metadata_key, state_name in config["frontmatter"].items():
        value = get(state_name)
        if entry_kind == "Waffe" and metadata_key == "Einstimmung":
            metadata[metadata_key] = str(value).casefold() in {"ja", "true", "yes"}
        else:
            metadata[metadata_key] = value if value != "" else None
    return metadata


def _field_value(entry_kind: str, field_name: str) -> str:
    return str(st.session_state.get(_state_key(entry_kind, field_name), "")).strip()


def _replace_body_line(body: str, label: str, value: str, style: str) -> str:
    prefix = rf"^[ \t]*-[ \t]*{re.escape(label)}:[ \t]*" if style == "plain" else (
        rf"^[ \t]*-[ \t]*\*\*{re.escape(label)}:\*\*[ \t]*"
    )
    pattern = re.compile(prefix + r".*$", re.MULTILINE)
    replacement_value = value if value else ""
    def replacement(match: re.Match[str]) -> str:
        prefix = match.group(0)[: match.group(0).find(":") + 1]
        value_text = replacement_value.replace("\n", "\n  ")
        return prefix + (f" {value_text}" if value_text else "")

    return pattern.sub(replacement, body, count=1)


def _replace_section(body: str, heading: str, value: str) -> str:
    heading_pattern = re.compile(
        rf"(?m)^(?P<heading>\s*#+\s*{re.escape(heading)}:?)\s*$"
    )
    match = heading_pattern.search(body)
    if not match:
        field_pattern = re.compile(
            rf"(?m)^(?P<prefix>[ \t]*-[ \t]*\*\*{re.escape(heading)}:\*\*)[ \t]*.*$"
        )
        field_match = field_pattern.search(body)
        if not field_match:
            return body
        replacement = field_match.group("prefix")
        if value.strip():
            replacement += f"\n\n{value.strip()}"
        return body[: field_match.start()] + replacement + body[field_match.end() :]
    next_heading = re.search(r"(?m)^\s*#+\s+", body[match.end() :])
    end = match.end() + next_heading.start() if next_heading else len(body)
    content = f"\n\n{value.strip()}\n\n" if value.strip() else "\n\n"
    return body[: match.end()] + content + body[end:]


def _render_entry_markdown(entry_kind: str) -> str:
    config = ENTRY_CONFIGS[entry_kind]
    template = (cfg.MARKDOWN_DIR / "templates" / config["template"]).read_text(
        encoding="utf-8"
    )
    metadata, body = split_frontmatter(template)
    metadata.update(_entry_metadata(entry_kind))

    for field_name, (label, style) in config.get("body_fields", {}).items():
        value = _field_value(entry_kind, "tags" if field_name == "tag" else field_name)
        if field_name == "tag" and value:
            value = " ".join(
                tag if tag.startswith("#") else f"#{tag}"
                for tag in re.split(r"[,\s]+", value)
                if tag
            )
        body = _replace_body_line(body, label, value, style)

    for field_name, heading in config.get("sections", {}).items():
        body = _replace_section(body, heading, _field_value(entry_kind, field_name))

    title = _field_value(entry_kind, "name") or "Unbenannter Eintrag"
    title_pattern = re.compile(r"(?m)^#\s+.*$")
    if title_pattern.search(body):
        body = title_pattern.sub(f"# {title}", body, count=1)
    else:
        body = f"# {title}\n\n{body.lstrip()}"

    return serialize_frontmatter(metadata) + body.lstrip()


def _destination_directory(entry_kind: str) -> Path:
    config = ENTRY_CONFIGS[entry_kind]
    destination = st.session_state.get(_state_key(entry_kind, "destination"), "Sammlung")
    if destination == "Spielleiter":
        return cfg.MARKDOWN_DIR / "Spielleiter"
    return cfg.MARKDOWN_DIR / config["collection"]


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", name).strip(" .")
    return cleaned or "Unbenannter Eintrag"


def _save_entry(entry_kind: str) -> tuple[bool, str]:
    name = _field_value(entry_kind, "name")
    if not name:
        return False, "Bitte zuerst einen Namen eingeben."
    destination = _destination_directory(entry_kind)
    export_path = destination / f"{_safe_filename(name)}.md"
    if export_path.exists():
        return False, f"Datei existiert bereits: {export_path.name}"
    destination.mkdir(parents=True, exist_ok=True)
    export_path.write_text(_render_entry_markdown(entry_kind), encoding="utf-8")
    return True, str(export_path.relative_to(cfg.REPO_ROOT))


def entry_creator_view(entry_kind: str) -> None:
    config = ENTRY_CONFIGS[entry_kind]
    _ensure_entry_state(entry_kind)
    st.subheader(f"{entry_kind} erstellen")
    form_col, preview_col = st.columns([3, 4], vertical_alignment="top")

    with form_col:
        with st.container(border=True):
            st.text_input("Name", key=_state_key(entry_kind, "name"))
            st.markdown("**Metadaten**")
            for name, label, default in COMMON_METADATA_FIELDS:
                key = _state_key(entry_kind, name)
                if name == "status":
                    st.text_input(label, key=key)
                elif name in {"start_year", "end_year"}:
                    continue
                else:
                    st.text_input(label, key=key)
            year_cols = st.columns(2)
            year_cols[0].text_input("Jahr von", key=_state_key(entry_kind, "start_year"))
            year_cols[1].text_input("Jahr bis", key=_state_key(entry_kind, "end_year"))
            st.markdown("**Eintragsdaten**")
            for field_name, label, field_type, placeholder in config["fields"]:
                key = _state_key(entry_kind, field_name)
                if field_type == "area":
                    st.text_area(label, key=key, placeholder=placeholder, height=100)
                elif field_type == "bool":
                    st.selectbox(label, ("Nein", "Ja"), key=key)
                else:
                    st.text_input(label, key=key, placeholder=placeholder)
            st.selectbox(
                "Ablage",
                ("Sammlung", "Spielleiter"),
                key=_state_key(entry_kind, "destination"),
                format_func=lambda value: (
                    f"World/{config['collection']}"
                    if value == "Sammlung"
                    else "World/Spielleiter"
                ),
            )
            if st.button(f"{entry_kind} speichern", use_container_width=True):
                success, message = _save_entry(entry_kind)
                if success:
                    st.success(f"Gespeichert: {message}")
                else:
                    st.warning(message)

    with preview_col:
        with st.container(border=True):
            st.markdown("**Vorschau**")
            metadata, body = split_frontmatter(_render_entry_markdown(entry_kind))
            st.table(metadata_display_rows(metadata))
            st.markdown(body)