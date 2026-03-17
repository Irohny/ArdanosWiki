from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scan_lore import (
    CURRENT_YEAR,
    OUTPUT_FILE,
    REPO_ROOT,
    load_scan_results,
    scan_lore,
    write_scan_results,
)
from validate_metadata import validate_item

SCRIPT_ROOT = Path(__file__).resolve().parent
ZEITALTER_FILE = REPO_ROOT / "World" / "Kaiserreich" / "Geschichte" / "Zeitalter.md"
TIMELINE_FILE = REPO_ROOT / "timeline_tools" / "vertical_svg" / "timeline_data.json"

COLUMN_META = {
    "world": {"label": "Zeit", "color": "#d8c38f", "lanes": 2, "width": 120},
    "emperor": {"label": "Ardanos", "color": "#c69c2d", "lanes": 2},
    "elmrath": {"label": "Elmrath", "color": "#7aa23f", "lanes": 2},
    "drakmora": {"label": "Drakmora", "color": "#b35c44", "lanes": 2},
    "mariven": {"label": "Mariven", "color": "#2f8a7f", "lanes": 2},
    "schwarzklamm": {"label": "Schwarzklamm", "color": "#4f5563", "lanes": 2},
    "vaylen": {"label": "Vaylen", "color": "#5f83b0", "lanes": 2},
}
CATEGORY_TO_COLUMN = {
    "Kaiserreich": "emperor",
    "Elmrath": "elmrath",
    "Drakmora": "drakmora",
    "Mariven": "mariven",
    "Schwarzklamm": "schwarzklamm",
    "Vaylen": "vaylen",
}
ERAS = [
    {"label": "Erstes Zeitalter", "start": 300, "end": 1230, "fill": "#f7f1df"},
    {"label": "Zweites Zeitalter", "start": 1231, "end": 2164, "fill": "#efe6d2"},
    {
        "label": "Drittes Zeitalter",
        "start": 2165,
        "end": CURRENT_YEAR,
        "fill": "#e8ddca",
    },
]
WORLD_ITEMS = [
    {
        "column": "world",
        "lane": 0,
        "label": "Erstes Zeitalter",
        "start": 300,
        "end": 1230,
        "kind": "range",
        "fill": "#e7d9b6",
    },
    {
        "column": "world",
        "lane": 0,
        "label": "Zweites Zeitalter",
        "start": 1231,
        "end": 2164,
        "kind": "range",
        "fill": "#dcc8a0",
    },
    {
        "column": "world",
        "lane": 0,
        "label": "Drittes Zeitalter",
        "start": 2165,
        "end": CURRENT_YEAR,
        "kind": "range",
        "fill": "#cfb27d",
    },
]


def lighten(hex_value: str, ratio: float) -> str:
    value = hex_value.lstrip("#")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    red = round(red + (255 - red) * ratio)
    green = round(green + (255 - green) * ratio)
    blue = round(blue + (255 - blue) * ratio)
    return f"#{red:02x}{green:02x}{blue:02x}"


def base_timeline() -> dict[str, Any]:
    return {
        "title": "Ardanos: Chronik des Reiches",
        "subtitle": "Geschichte der Kaiser und Fürstenhäuser",
        "min_year": 300,
        "max_year": CURRENT_YEAR,
        "pixels_per_year": 0.58,
        "tick_year_step": 100,
        "columns": [
            {"id": column_id, **meta} for column_id, meta in COLUMN_META.items()
        ],
        "eras": ERAS,
        "items": list(WORLD_ITEMS),
    }


def load_payload() -> dict[str, Any]:
    if OUTPUT_FILE.exists():
        return load_scan_results()
    payload = scan_lore()
    write_scan_results(payload)
    return payload


def buildable_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in payload["items"]:
        if not item["is_relevant"]:
            continue
        errors = validate_item(item)
        if errors:
            continue
        items.append(item)
    return items


def parse_shield_age_item() -> dict[str, Any]:
    text = ZEITALTER_FILE.read_text(encoding="utf-8")
    if "Seit 2410 n.d.D" not in text:
        return {}
    return {
        "column": "schwarzklamm",
        "lane": 1,
        "label": "Zeitalter des Schildes",
        "start": 2410,
        "end": CURRENT_YEAR,
        "kind": "range",
        "fill": lighten(COLUMN_META["schwarzklamm"]["color"], 0.2),
    }


def foundation_item(item: dict[str, Any]) -> dict[str, Any] | None:
    category = item["categories"][0]
    column = CATEGORY_TO_COLUMN.get(category)
    if column is None:
        return None
    return {
        "column": column,
        "label": f"Gruendung {category}",
        "start": item["parsed_timespan"]["start"],
        "end": item["parsed_timespan"]["end"],
        "kind": "foundation",
    }


def ruler_item(item: dict[str, Any]) -> dict[str, Any] | None:
    category = item["categories"][0]
    column = CATEGORY_TO_COLUMN.get(category)
    if column is None:
        return None
    return {
        "column": column,
        "lane": 0,
        "label": item["title"],
        "start": item["parsed_timespan"]["start"],
        "end": item["parsed_timespan"]["end"],
        "kind": "range",
    }


def local_event_items(item: dict[str, Any]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    parsed_timespan = item["parsed_timespan"]
    for category in item["categories"]:
        column = CATEGORY_TO_COLUMN.get(category)
        if column is None:
            continue
        built.append(
            {
                "column": column,
                "lane": 1,
                "label": item["title"],
                "start": parsed_timespan["start"],
                "end": parsed_timespan["end"],
                "kind": parsed_timespan["kind"],
                "fill": lighten(COLUMN_META[column]["color"], 0.2),
            }
        )
    return built


def build_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    for item in items:
        primary_type = item["primary_types"][0]
        if primary_type == "Gruendung":
            foundation = foundation_item(item)
            if foundation:
                built.append(foundation)
            continue
        if primary_type == "Herrscher":
            ruler = ruler_item(item)
            if ruler:
                built.append(ruler)
            continue
        if any(category in CATEGORY_TO_COLUMN for category in item["categories"]):
            built.extend(local_event_items(item))
    return built


def sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    order = list(COLUMN_META).index(item["column"])
    return (order, item.get("lane", -1), item["start"], item["label"])


def main() -> None:
    payload = load_payload()
    items = buildable_items(payload)

    timeline = base_timeline()
    shield_age = parse_shield_age_item()
    if shield_age:
        timeline["items"].append(shield_age)
    timeline["items"].extend(build_items(items))
    timeline["items"] = sorted(timeline["items"], key=sort_key)

    TIMELINE_FILE.write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {TIMELINE_FILE.relative_to(REPO_ROOT)}")
    print(f"Built {len(timeline['items'])} timeline items.")


if __name__ == "__main__":
    main()
