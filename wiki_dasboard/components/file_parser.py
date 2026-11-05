from pathlib import Path

import pandas as pd
import re
import yaml

DATABASE_FIELDS = {
    "Bestiarium": {
        "Stufe": "stufe",
        "Volk": "volk",
        "Gesinnung": "gesinnung",
        "Rüstungsklasse": "ruestungsklasse",
        "Grundlage": "grundlage",
    },
    "Zauberarchiv": {
        "Grad": "grad",
        "Schule": "schule",
        "Konzentration": "konzentration",
        "Komponenten": "komponenten",
        "Materialien": "materialien",
    },
    "Tranksammlung": {
        "Tags": "tags",
        "Wert": "wert",
        "Komponenten": "komponenten",
        "Seltenheit": "seltenheit",
    },
    "Zutatenarchiv": {
        "Seltenheit": "seltenheit",
        "Wert": "wert",
        "Fundort": "fundort",
    },
    "Waffenkammer": {
        "Waffentyp": "Waffentyp",
        "Schadensart": "Schadensart",
        "Kategorie": "Kategorie",
        "Seltenheit": "Seltenheit",
        "Wert": "Wert",
        "Reichweite": "Reichweite",
        "Einstimmung": "Einstimmung",
        "Sichtbarkeit": "sichtbarkeit",
    },
    "Schatzkammer": {
        "Seltenheit": "seltenheit",
        "Einstimmung": "einstimmung",
        "Kategorie": "kategorie",
        "Wert": "wert",
        "Sichtbarkeit": "sichtbarkeit",
    },
}

BODY_DATABASE_FIELDS = {
    "Waffenkammer": {
        "Schaden": "Schaden",
        "Gewicht": "Gewicht",
        "Voraussetzung": "Voraussetzung",
        "Fundort": "Fundort",
        "Eigenschaften": "Besondere Eigenschaften",
    },
    "Schatzkammer": {
        "Voraussetzung": "Voraussetzung",
        "Ladungen": "Ladungen",
        "Aufladung": "Aufladung",
        "Fundort": "Fundort",
        "Eigenschaften": "Eigenschaften und Kräfte",
    },
}


def get_dict(root: str, name: str, path: str) -> tuple[dict, dict[str, str]]:
    category = next(
        (
            category
            for category in (*DATABASE_FIELDS, *BODY_DATABASE_FIELDS)
            if category.casefold() in root.casefold()
        ),
        None,
    )
    fields = DATABASE_FIELDS.get(category, {})
    body_fields = BODY_DATABASE_FIELDS.get(category, {})
    data: dict[str, object] = {"Name": name, "Pfad": path}
    data.update({field: None for field in fields})
    data.update({field: None for field in body_fields})
    return data, fields


def _read_document(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("\ufeff"):
        text = text[1:]
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not match:
        return {}, text

    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        metadata = {}
    return metadata if isinstance(metadata, dict) else {}, text[match.end() :]


def _read_body_field(body: str, label: str) -> str | None:
    match = re.search(
        rf"(?m)^[ \t]*[-*][ \t]+\*\*{re.escape(label)}:\*\*[ \t]*([^\r\n]*?)[ \t]*$",
        body,
    )
    if not match:
        return None
    return match.group(1).strip() or None


def _read_body_section(body: str, heading: str) -> str | None:
    match = re.search(rf"(?m)^##\s+{re.escape(heading)}\s*$", body)
    if not match:
        return None

    section = body[match.end() :]
    next_heading = re.search(r"(?m)^#{1,6}\s+", section)
    if next_heading:
        section = section[: next_heading.start()]

    items = re.findall(r"(?m)^\s*[-*]\s+(.+?)\s*$", section)
    return "; ".join(item.strip() for item in items) or None


def _format_metadata_value(value, field: str):
    if isinstance(value, list):
        values = [str(item).strip() for item in value if str(item).strip()]
        if field == "Tags":
            return " ".join(f"#{tag.lstrip('#')}" for tag in values if tag.lstrip("#"))
        return ", ".join(values)
    if value is None:
        return None
    if field in {"Stufe", "Grad"}:
        return str(value)
    if field == "Rüstungsklasse":
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    return value


def parse_markdown_file(path: Path, root: str) -> dict:
    """
    Liest Datenbankfelder aus YAML-Frontmatter und beschrifteten Textfeldern.
    """
    data, field_map = get_dict(root, path.stem, str(path.resolve()))
    metadata, body = _read_document(path)

    for field, metadata_key in field_map.items():
        data[field] = _format_metadata_value(metadata.get(metadata_key), field)

    category = next(
        (
            name
            for name in BODY_DATABASE_FIELDS
            if name.casefold() in root.casefold()
        ),
        None,
    )
    for field, label in BODY_DATABASE_FIELDS.get(category, {}).items():
        if field == "Eigenschaften":
            data[field] = _read_body_section(body, label)
        else:
            data[field] = _read_body_field(body, label)

    return data


def build_markdown_database(root_path: str) -> pd.DataFrame:
    """
    Durchsucht rekursiv root_path nach Markdown-Dateien
    und erstellt einen DataFrame mit den extrahierten Daten.
    """
    root = Path(root_path)
    records = []

    for md_file in root.rglob("*.md"):
        try:
            record = parse_markdown_file(md_file, root_path)
            records.append(record)
        except Exception as e:
            print(f"⚠️ Fehler beim Parsen von {md_file}: {e}")

    schema, _ = get_dict(root_path, "", "")
    return pd.DataFrame(records, columns=list(schema))
