from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent.parent
LORE_ROOT = REPO_ROOT / "World" / "Kaiserreich"
OUTPUT_FILE = SCRIPT_ROOT / "extracted_items.json"
CURRENT_YEAR = 2486

PRIMARY_TYPES = {"Herrscher", "Krieg", "Konflikt", "Gruendung", "Ereignis"}
CATEGORY_ORDER = [
    "Weltgeschichte",
    "Kaiserreich",
    "Elmrath",
    "Drakmora",
    "Mariven",
    "Schwarzklamm",
    "Vaylen",
]
CATEGORY_SET = set(CATEGORY_ORDER)
MAX_METADATA_LINES = 12
TIMESPAN_RE = re.compile(
    r"^(?:Zeitspanne:\s*)?(?P<start>\d{1,4})(?:\s*-\s*(?P<end>\d{1,4}|heute))?\s*n\.d\.D\.?$",
    re.IGNORECASE,
)
BULLET_FIELD_RE = re.compile(
    r"^\s*-\s+\*\*(?P<field>[^*:]+?)(?::)?\*\*:?\s*(?P<value>.*)$"
)
FIELD_CATEGORY_SPLIT_RE = re.compile(r"\s*,\s*|\s+/\s+")
RULER_TITLE_RE = re.compile(
    r"\b(?:fuerst|fürst|fuerstin|fürstin|kaiser|kaiserin)\b",
    re.IGNORECASE,
)
TRACKED_FIELD_ALIASES = {
    "Name": "Name",
    "Rufname / Beiname": "Rufname / Beiname",
    "Titel": "Titel / Amt",
    "Title": "Titel / Amt",
    "Titel / Amt": "Titel / Amt",
    "Haus": "Haus / Dynastie",
    "Haus / Dynastie": "Haus / Dynastie",
    "Linie / Nebenlinie": "Linie / Nebenlinie",
    "Primaertyp": "Primaertyp",
    "Zeitachsen-Kategorie": "Zeitachsen-Kategorie",
    "Zeitachsen-Label": "Zeitachsen-Label",
    "Zeitspanne": "Zeitspanne",
    "Primaere Zeitspanne": "Primaere Zeitspanne",
    "Regentschaft": "Regentschaft",
    "Regentschaft als Kaiser": "Regentschaft als Kaiser",
    "Regentschaft im Fuerstentum / Lehen": "Regentschaft im Fuerstentum / Lehen",
    "Vorgaenger": "Vorgaenger",
    "Nachfolger": "Nachfolger",
    "Status": "Status",
    "Rasse": "Spezies / Volk",
    "Spezies / Volk": "Spezies / Volk",
    "Herkunft": "Herkunft",
    "Derzeitiger Sitz / Aufenthaltsort": "Derzeitiger Sitz / Aufenthaltsort",
    "Geburtsjahr": "Geburtsjahr",
    "Sterbejahr": "Sterbejahr",
    "Alter": "Alter",
    "Verknuepfte Orte": "Verknuepfte Orte",
    "Verknuepfte NPCs": "Verknuepfte NPCs",
    "Bekannt fuer": "Bekannt fuer",
    "Erste Erwaehnung": "Erste Erwaehnung",
    "Tags": "Tags",
}


def is_tag_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("# "):
        return False
    tokens = stripped.split()
    return all(
        token.startswith("#") and len(token) > 1 and not token.startswith("# ")
        for token in tokens
    )


def leading_metadata_lines(text: str) -> list[str]:
    lines = text.splitlines()
    collected: list[str] = []
    for raw_line in lines[:MAX_METADATA_LINES]:
        stripped = raw_line.strip()
        if not stripped:
            if collected:
                collected.append(raw_line)
            continue
        if is_tag_line(stripped) or stripped.startswith("Zeitspanne:"):
            collected.append(raw_line)
            continue
        if collected:
            break
        return []
    return collected


def normalize_timespan(raw: str) -> dict[str, Any] | None:
    raw = raw.strip().replace("–", "-").replace("—", "-")
    if raw.lower().startswith("seit "):
        raw = f"{raw[5:].strip()} - heute n.d.D."
    match = TIMESPAN_RE.match(raw.strip())
    if not match:
        return None

    start = int(match.group("start"))
    end_token = match.group("end")
    if end_token is None:
        return {
            "kind": "point",
            "start": start,
            "end": start,
            "is_open": False,
        }

    if end_token.lower() == "heute":
        return {
            "kind": "range",
            "start": start,
            "end": CURRENT_YEAR,
            "is_open": True,
        }

    end = int(end_token)
    return {
        "kind": "range",
        "start": start,
        "end": end,
        "is_open": False,
    }


def normalize_field_name(raw: str) -> str:
    normalized = re.sub(r"\s+", " ", raw.strip().rstrip(":"))
    return TRACKED_FIELD_ALIASES.get(normalized, normalized)


def extract_bullet_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in text.splitlines():
        match = BULLET_FIELD_RE.match(raw_line)
        if not match:
            continue
        field_name = normalize_field_name(match.group("field"))
        if field_name not in TRACKED_FIELD_ALIASES.values():
            continue
        fields.setdefault(field_name, match.group("value").strip())
    return fields


def parse_declared_categories(raw: str) -> list[str]:
    if not raw:
        return []
    parts = FIELD_CATEGORY_SPLIT_RE.split(raw.strip())
    return [part for part in parts if part in CATEGORY_SET]


def parse_primary_types(raw: str) -> list[str]:
    if not raw:
        return []
    parts = FIELD_CATEGORY_SPLIT_RE.split(raw.strip())
    return [part for part in parts if part in PRIMARY_TYPES]


def infer_primary_types_from_fields(fields: dict[str, str]) -> list[str]:
    explicit = parse_primary_types(fields.get("Primaertyp", ""))
    if explicit:
        return explicit
    title_or_office = fields.get("Titel / Amt", "").strip()
    if title_or_office and RULER_TITLE_RE.search(title_or_office):
        return ["Herrscher"]
    if any(
        fields.get(key, "").strip()
        for key in (
            "Regentschaft",
            "Regentschaft als Kaiser",
            "Regentschaft im Fuerstentum / Lehen",
        )
    ):
        return ["Herrscher"]
    return []


def field_timespan_candidates(fields: dict[str, str]) -> list[str]:
    candidates: list[str] = []
    for key in (
        "Zeitspanne",
        "Primaere Zeitspanne",
        "Regentschaft",
        "Regentschaft als Kaiser",
        "Regentschaft im Fuerstentum / Lehen",
    ):
        value = fields.get(key, "").strip()
        if value:
            candidates.append(value)
    return candidates


def infer_categories(path: Path) -> list[str]:
    relative_parts = path.relative_to(LORE_ROOT).parts
    if relative_parts and relative_parts[0] == "Kaiser":
        return ["Kaiserreich"]
    matches = [
        category
        for category in CATEGORY_ORDER
        if category in relative_parts or path.stem == category
    ]
    if matches:
        return matches
    return []


def extract_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata_lines = leading_metadata_lines(text)
    bullet_fields = extract_bullet_fields(text)
    tag_tokens: list[str] = []
    timespan_lines: list[str] = []

    for raw_line in metadata_lines:
        stripped = raw_line.strip()
        if is_tag_line(stripped):
            tag_tokens.extend(stripped.split())
        elif stripped.startswith("Zeitspanne:"):
            timespan_lines.append(stripped)

    header_primary_types = [
        token[1:] for token in tag_tokens if token[1:] in PRIMARY_TYPES
    ]
    header_declared_categories = [
        token[1:] for token in tag_tokens if token[1:] in CATEGORY_SET
    ]
    field_primary_types = infer_primary_types_from_fields(bullet_fields)
    field_declared_categories = parse_declared_categories(
        bullet_fields.get("Zeitachsen-Kategorie", "")
    )
    primary_types = header_primary_types or field_primary_types
    declared_categories = header_declared_categories or field_declared_categories
    fallback_categories = infer_categories(path)
    categories = declared_categories or fallback_categories
    timespan_candidates = timespan_lines or field_timespan_candidates(bullet_fields)
    timespan_raw = timespan_candidates[0] if timespan_candidates else None
    title = bullet_fields.get("Name") or path.stem
    timeline_label = bullet_fields.get("Zeitachsen-Label") or title

    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "title": title,
        "timeline_label": timeline_label,
        "primary_types": primary_types,
        "declared_categories": list(dict.fromkeys(declared_categories)),
        "fallback_categories": list(dict.fromkeys(fallback_categories)),
        "categories": list(dict.fromkeys(categories)),
        "timespan_line_count": len(timespan_candidates),
        "timespan_raw": timespan_raw,
        "parsed_timespan": normalize_timespan(timespan_raw) if timespan_raw else None,
        "metadata_lines": metadata_lines,
        "metadata_source": (
            "header" if metadata_lines else ("fields" if primary_types else "none")
        ),
        "structured_fields": bullet_fields,
        "is_relevant": bool(primary_types),
    }


def scan_lore() -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for path in sorted(LORE_ROOT.rglob("*.md")):
        items.append(extract_metadata(path))
    return {
        "lore_root": str(LORE_ROOT.relative_to(REPO_ROOT)),
        "current_year": CURRENT_YEAR,
        "items": items,
    }


def write_scan_results(payload: dict[str, Any]) -> None:
    OUTPUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load_scan_results() -> dict[str, Any]:
    return json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))


def main() -> None:
    payload = scan_lore()
    write_scan_results(payload)
    relevant_count = sum(1 for item in payload["items"] if item["is_relevant"])
    print(f"Scanned {len(payload['items'])} markdown files.")
    print(f"Found {relevant_count} metadata-tagged files.")
    print(f"Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
