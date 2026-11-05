from __future__ import annotations

import re
from typing import Any

import yaml


FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\r?\n(?P<metadata>.*?)\r?\n---\s*(?:\r?\n|\Z)(?P<body>.*)\Z",
    re.DOTALL,
)
TIME_RANGE_PATTERN = re.compile(
    r"^(?:(?:ab|seit)\s+)?(?P<start>\d{1,4})"
    r"(?:\s*(?:-|–|—|bis)\s*(?P<end>\d{1,4}|heute))?"
    r"\s*n\.d\.D\.?$",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"^\s*(\d{1,4})")


def split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_PATTERN.match(content)
    if match is None:
        return {}, content

    try:
        metadata = yaml.safe_load(match.group("metadata")) or {}
    except yaml.YAMLError:
        metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, match.group("body")


def replace_frontmatter(content: str, metadata: dict[str, Any]) -> str:
    existing_metadata, body = split_frontmatter(content)
    merged_metadata = dict(existing_metadata)
    merged_metadata.update(metadata)
    serialized_metadata = yaml.safe_dump(
        merged_metadata,
        allow_unicode=True,
        sort_keys=False,
    ).rstrip()
    return f"---\n{serialized_metadata}\n---\n{body.lstrip()}"


def serialize_frontmatter(metadata: dict[str, Any]) -> str:
    serialized_metadata = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
    ).rstrip()
    return f"---\n{serialized_metadata}\n---\n"


def metadata_values_to_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        values = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(values)
    if value is None:
        return ""
    return str(value).strip()


METADATA_DISPLAY_LABELS = {
    "typ": "Typ",
    "status": "Status",
    "kampagne": "Kampagne",
    "region": "Region",
    "tags": "Tags",
    "zeit_text": "Zeit",
    "zeit_von_jahr": "Jahr von",
    "zeit_bis_jahr": "Jahr bis",
    "erstellt": "Erstellt",
    "geaendert": "Geaendert",
    "stufe": "Stufe",
    "volk": "Volk",
    "gesinnung": "Gesinnung",
    "ruestungsklasse": "Ruestungsklasse",
    "grundlage": "Grundlage",
}


def metadata_display_rows(metadata: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for key, label in METADATA_DISPLAY_LABELS.items():
        value = metadata.get(key)
        if value is None or value == "" or value == []:
            continue
        rows.append({"Metadatum": label, "Wert": metadata_values_to_text(value)})
    return rows


def _input_values(value: Any, *, split_whitespace: bool = False) -> list[str]:
    if isinstance(value, (list, tuple)):
        raw_values = [str(item) for item in value]
    elif value is None:
        raw_values = []
    else:
        raw_values = [str(value)]

    values: list[str] = []
    for raw_value in raw_values:
        parts = re.split(r"[,\s]+", raw_value) if split_whitespace else raw_value.split(",")
        values.extend(part.strip() for part in parts if part.strip())
    return values


def normalize_metadata_links(value: Any) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for entry in _input_values(value):
        if entry.startswith("[[") and entry.endswith(']]'):
            link = entry
        else:
            link = f"[[{entry}]]"
        if link.casefold() not in seen:
            links.append(link)
            seen.add(link.casefold())
    return links


def normalize_metadata_regions(value: Any) -> str | list[str] | None:
    regions = _input_values(value)
    if not regions:
        return None
    return regions[0] if len(regions) == 1 else regions


def normalize_metadata_tags(value: Any) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for entry in _input_values(value, split_whitespace=True):
        tag = entry.strip().removeprefix("#")
        if tag.startswith("[[") and tag.endswith("]]" ):
            tag = tag[2:-2].strip()
        if tag and tag.casefold() not in seen:
            tags.append(tag)
            seen.add(tag.casefold())
    return tags


def _year_value(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    match = YEAR_PATTERN.match(str(value or ""))
    return int(match.group(1)) if match else None


def build_time_metadata(
    time_text: Any,
    start_year: Any,
    end_year: Any,
    *,
    fallback_start: Any = None,
    fallback_end: Any = None,
) -> dict[str, Any]:
    normalized_text = str(time_text or "").strip()
    start = _year_value(start_year) or _year_value(fallback_start)
    end = _year_value(end_year) or _year_value(fallback_end)

    time_match = TIME_RANGE_PATTERN.fullmatch(normalized_text)
    if time_match:
        start = start or int(time_match.group("start"))
        end_token = time_match.group("end")
        if end is None and end_token and end_token.casefold() != "heute":
            end = int(end_token)

    if not normalized_text and start is not None:
        if end is not None:
            normalized_text = f"{start}–{end} n.d.D."
        else:
            normalized_text = f"ab {start} n.d.D."

    return {
        "zeit_text": normalized_text or None,
        "zeit_von_jahr": start,
        "zeit_bis_jahr": end,
    }