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
    r"^Zeitspanne:\s*(?P<start>\d{1,4})(?:\s*-\s*(?P<end>\d{1,4}|heute))?\s*n\.d\.D\.?$",
    re.IGNORECASE,
)


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


def infer_categories(path: Path) -> list[str]:
    relative_parts = path.relative_to(LORE_ROOT).parts
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
    tag_tokens: list[str] = []
    timespan_lines: list[str] = []

    for raw_line in metadata_lines:
        stripped = raw_line.strip()
        if is_tag_line(stripped):
            tag_tokens.extend(stripped.split())
        elif stripped.startswith("Zeitspanne:"):
            timespan_lines.append(stripped)

    primary_types = [token[1:] for token in tag_tokens if token[1:] in PRIMARY_TYPES]
    declared_categories = [
        token[1:] for token in tag_tokens if token[1:] in CATEGORY_SET
    ]
    fallback_categories = infer_categories(path)
    categories = declared_categories or fallback_categories
    timespan_raw = timespan_lines[0] if len(timespan_lines) == 1 else None

    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "title": path.stem,
        "primary_types": primary_types,
        "declared_categories": list(dict.fromkeys(declared_categories)),
        "fallback_categories": list(dict.fromkeys(fallback_categories)),
        "categories": list(dict.fromkeys(categories)),
        "timespan_line_count": len(timespan_lines),
        "timespan_raw": timespan_raw,
        "parsed_timespan": normalize_timespan(timespan_raw) if timespan_raw else None,
        "metadata_lines": metadata_lines,
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
