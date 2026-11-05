from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORLD_ROOT = REPO_ROOT / "World"
CURRENT_YEAR = 2486

TIMELINE_DIR = Path(__file__).resolve().parents[1] / "vertical_svg"
TIMELINE_OUTPUT_DIR = WORLD_ROOT / "Images" / "Timelines"
TIME_COLUMN_WIDTH = 57
ORIGINAL_TIME_COLUMN_WIDTH = 120
DEFAULT_COLUMN_WIDTH = 155

REALM_COLUMN_META = {
    "world": {
        "label": "Zeit",
        "color": "#d8c38f",
        "lanes": 1,
        "width": TIME_COLUMN_WIDTH,
        "label_mode": "event",
    },
    "emperor": {
        "label": "Ardanos",
        "color": "#c69c2d",
        "lanes": 2,
        "label_mode": "person",
    },
    "elmrath": {
        "label": "Elmrath",
        "color": "#7aa23f",
        "lanes": 2,
        "label_mode": "person",
    },
    "drakmora": {
        "label": "Drakmora",
        "color": "#b35c44",
        "lanes": 2,
        "label_mode": "person",
    },
    "mariven": {
        "label": "Mariven",
        "color": "#2f8a7f",
        "lanes": 2,
        "label_mode": "person",
    },
    "schwarzklamm": {
        "label": "Schwarzklamm",
        "color": "#4f5563",
        "lanes": 2,
        "label_mode": "person",
    },
    "vaylen": {
        "label": "Vaylen",
        "color": "#5f83b0",
        "lanes": 2,
        "label_mode": "person",
    },
}
REALM_CATEGORY_TO_COLUMN = {
    "Weltgeschichte": "world",
    "Kaiserreich": "emperor",
    "Elmrath": "elmrath",
    "Drakmora": "drakmora",
    "Mariven": "mariven",
    "Schwarzklamm": "schwarzklamm",
    "Vaylen": "vaylen",
}
REALM_TAG_TO_CATEGORY = {
    "ardanos": "Kaiserreich",
    "kaiser": "Kaiserreich",
    "kaiserreich": "Kaiserreich",
    "weltgeschichte": "Weltgeschichte",
    "elmrath": "Elmrath",
    "drakmora": "Drakmora",
    "mariven": "Mariven",
    "schwarzklamm": "Schwarzklamm",
    "vaylen": "Vaylen",
}
TIMELINE_EVENT_TAGS = {
    "ergeignis",
    "ereignis",
    "ereignisse",
    "geschichte",
    "krieg",
    "konflikt",
}
RULER_TAGS = {"fürst", "fuerst", "herrscher", "kaiser", "könig", "koenig"}
FOUNDATION_TAGS = {"gründung", "gruendung"}
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
PRINCIPALITY_META = {
    "elmrath": {"category": "Elmrath", "label": "Elmrath", "color": "#7aa23f"},
    "drakmora": {"category": "Drakmora", "label": "Drakmora", "color": "#b35c44"},
    "mariven": {"category": "Mariven", "label": "Mariven", "color": "#2f8a7f"},
    "schwarzklamm": {
        "category": "Schwarzklamm",
        "label": "Schwarzklamm",
        "color": "#4f5563",
    },
    "vaylen": {"category": "Vaylen", "label": "Vaylen", "color": "#5f83b0"},
}


def lighten(hex_value: str, ratio: float) -> str:
    value = hex_value.lstrip("#")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    red = round(red + (255 - red) * ratio)
    green = round(green + (255 - green) * ratio)
    blue = round(blue + (255 - blue) * ratio)
    return f"#{red:02x}{green:02x}{blue:02x}"


def realm_profile() -> dict[str, Any]:
    redistributed_width = (ORIGINAL_TIME_COLUMN_WIDTH - TIME_COLUMN_WIDTH) / (
        len(REALM_COLUMN_META) - 1
    )
    columns = []
    for column_id, meta in REALM_COLUMN_META.items():
        column = {"id": column_id, **meta}
        if column_id != "world":
            column["width"] = DEFAULT_COLUMN_WIDTH + redistributed_width
        columns.append(column)

    return {
        "id": "realm",
        "type": "realm",
        "title": "Ardanos: Chronik des Reiches",
        "subtitle": "Geschichte der Kaiser und Fürstenhäuser",
        "min_year": 300,
        "max_year": CURRENT_YEAR,
        "pixels_per_year": 0.58,
        "tick_year_step": 100,
        "columns": columns,
        "eras": ERAS,
        "items": list(WORLD_ITEMS),
        "data_file": TIMELINE_DIR / "timeline_data.json",
        "output_file": TIMELINE_OUTPUT_DIR / "ardanos_vertical_timeline.svg",
    }


def principality_profile(profile_id: str, meta: dict[str, str]) -> dict[str, Any]:
    rulers_column = f"{profile_id}_rulers"
    ranges_column = f"{profile_id}_ranges"
    points_column = f"{profile_id}_points"
    color = meta["color"]
    label = meta["label"]
    redistributed_width = (ORIGINAL_TIME_COLUMN_WIDTH - TIME_COLUMN_WIDTH) / 3

    return {
        "id": profile_id,
        "type": "principality",
        "title": f"{label}: Chronik des Fürstentums",
        "subtitle": f"Geschichte des Fürstentums {label}",
        "min_year": 300,
        "max_year": CURRENT_YEAR,
        "pixels_per_year": 0.58,
        "tick_year_step": 100,
        "columns": [
            {
                "id": "world",
                "label": "Zeit",
                "color": "#d8c38f",
                "lanes": 1,
                "width": TIME_COLUMN_WIDTH,
                "label_mode": "event",
            },
            {
                "id": rulers_column,
                "label": f"{label} Fürsten",
                "color": color,
                "lanes": 1,
                "width": 170 + redistributed_width,
                "label_mode": "person",
            },
            {
                "id": ranges_column,
                "label": f"{label} Zeitspannen",
                "color": lighten(color, 0.08),
                "lanes": 1,
                "width": DEFAULT_COLUMN_WIDTH + redistributed_width,
                "label_mode": "event",
            },
            {
                "id": points_column,
                "label": f"{label} Zeitpunkte",
                "color": lighten(color, 0.16),
                "lanes": 1,
                "width": DEFAULT_COLUMN_WIDTH + redistributed_width,
                "label_mode": "event",
            },
        ],
        "eras": ERAS,
        "items": list(WORLD_ITEMS),
        "local_category": meta["category"],
        "ruler_column": rulers_column,
        "range_column": ranges_column,
        "point_column": points_column,
        "data_file": TIMELINE_DIR / f"timeline_data_{profile_id}.json",
        "output_file": TIMELINE_OUTPUT_DIR / f"{profile_id}_vertical_timeline.svg",
    }


def load_profiles() -> dict[str, dict[str, Any]]:
    profiles = {"realm": realm_profile()}
    for profile_id, meta in PRINCIPALITY_META.items():
        profiles[profile_id] = principality_profile(profile_id, meta)
    return profiles


def base_timeline(profile: dict[str, Any]) -> dict[str, Any]:
    timeline = {
        "profile_id": profile["id"],
        "title": profile["title"],
        "subtitle": profile["subtitle"],
        "min_year": profile["min_year"],
        "max_year": profile["max_year"],
        "pixels_per_year": profile["pixels_per_year"],
        "tick_year_step": profile["tick_year_step"],
        "columns": profile["columns"],
        "eras": profile["eras"],
        "items": list(profile["items"]),
        "output_file": str(profile["output_file"].relative_to(REPO_ROOT)),
    }
    return timeline


def normalize_tags(raw_tags: Any) -> set[str]:
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    if not isinstance(raw_tags, list):
        return set()

    tags = set()
    for raw_tag in raw_tags:
        tag = str(raw_tag).strip().casefold()
        if tag.startswith("#"):
            tag = tag[1:]
        if tag.startswith("[[") and tag.endswith("]]" ):
            tag = tag[2:-2].split("|", 1)[0].strip()
        tags.add(tag)
    return tags


def path_category(path: Path, world_root: Path = WORLD_ROOT) -> str | None:
    relative_parts = path.relative_to(world_root).parts
    if not relative_parts or relative_parts[0] != "Kaiserreich":
        return None
    if len(relative_parts) == 2 and path.stem.casefold() == "ardanos":
        return "Kaiserreich"
    if len(relative_parts) < 3:
        return None
    return REALM_TAG_TO_CATEGORY.get(relative_parts[1].casefold())


def is_canonical_foundation_page(path: Path, world_root: Path) -> bool:
    relative_parts = path.relative_to(world_root).parts
    if len(relative_parts) == 2:
        return (
            relative_parts[0] == "Kaiserreich"
            and path.stem.casefold() == "ardanos"
        )
    return (
        len(relative_parts) == 3
        and relative_parts[0] == "Kaiserreich"
        and relative_parts[1].casefold() in REALM_TAG_TO_CATEGORY
        and path.stem.casefold() == relative_parts[1].casefold()
    )


def parse_year(value: Any) -> int | None:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_timeline_page(
    path: Path, world_root: Path = WORLD_ROOT
) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    _, _, remainder = text.partition("---")
    frontmatter, separator, _ = remainder.partition("---")
    if not separator:
        return None
    metadata = yaml.safe_load(frontmatter) or {}
    if not isinstance(metadata, dict):
        return None

    start = parse_year(metadata.get("zeit_von_jahr"))
    if start is None:
        return None
    end = parse_year(metadata.get("zeit_bis_jahr"))
    tags = normalize_tags(metadata.get("tags"))
    region_values = normalize_tags(metadata.get("region")) | normalize_tags(
        metadata.get("Region")
    )

    if tags & RULER_TAGS:
        primary_type = "Herrscher"
        end = end if end is not None else CURRENT_YEAR
        kind = "range"
    elif tags & FOUNDATION_TAGS or is_canonical_foundation_page(path, world_root):
        primary_type = "Gruendung"
        end = start
        kind = "point"
    elif tags & TIMELINE_EVENT_TAGS and not tags & {"maler", "kunst"}:
        primary_type = "Ereignis"
        end = end if end is not None else start
        kind = "point" if end == start else "range"
    else:
        return None

    if end < start:
        return None

    categories = list(
        dict.fromkeys(
            category
            for tag, category in REALM_TAG_TO_CATEGORY.items()
            if tag in tags or tag in region_values
        )
    )
    if not categories:
        category = path_category(path, world_root)
        if category:
            categories = [category]
    if not categories:
        return None

    return {
        "title": path.stem,
        "primary_types": [primary_type],
        "categories": list(dict.fromkeys(categories)),
        "parsed_timespan": {"kind": kind, "start": start, "end": end},
    }


def load_payload(world_root: Path = WORLD_ROOT) -> dict[str, Any]:
    items = []
    for path in sorted(world_root.rglob("*.md")):
        item = parse_timeline_page(path, world_root)
        if item:
            items.append(item)
    return {"items": items}


def item_label(item: dict[str, Any]) -> str:
    return item["title"]


def buildable_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload["items"]


def realm_foundation_item(item: dict[str, Any]) -> dict[str, Any] | None:
    category = item["categories"][0]
    column = REALM_CATEGORY_TO_COLUMN.get(category)
    if column is None:
        return None
    return {
        "column": column,
        "label": f"Gruendung {category}",
        "start": item["parsed_timespan"]["start"],
        "end": item["parsed_timespan"]["end"],
        "kind": "foundation",
    }


def realm_ruler_item(item: dict[str, Any]) -> dict[str, Any] | None:
    category = item["categories"][0]
    column = REALM_CATEGORY_TO_COLUMN.get(category)
    if column is None:
        return None
    return {
        "column": column,
        "lane": 0,
        "label": item_label(item),
        "start": item["parsed_timespan"]["start"],
        "end": item["parsed_timespan"]["end"],
        "kind": "range",
    }


def realm_local_event_items(item: dict[str, Any]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    parsed_timespan = item["parsed_timespan"]
    for category in item["categories"]:
        column = REALM_CATEGORY_TO_COLUMN.get(category)
        if column is None:
            continue
        built.append(
            {
                "column": column,
                "lane": 0 if column == "world" else 1,
                "label": item_label(item),
                "start": parsed_timespan["start"],
                "end": parsed_timespan["end"],
                "kind": parsed_timespan["kind"],
                "fill": lighten(REALM_COLUMN_META[column]["color"], 0.2),
            }
        )
    return built


def build_realm_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    for item in items:
        primary_type = item["primary_types"][0]
        if primary_type == "Gruendung":
            foundation = realm_foundation_item(item)
            if foundation:
                built.append(foundation)
            continue
        if primary_type == "Herrscher":
            ruler = realm_ruler_item(item)
            if ruler:
                built.append(ruler)
            continue
        if any(category in REALM_CATEGORY_TO_COLUMN for category in item["categories"]):
            built.extend(realm_local_event_items(item))
    return built


def build_local_event_item(
    item: dict[str, Any],
    profile: dict[str, Any],
    color: str,
) -> dict[str, Any]:
    parsed_timespan = item["parsed_timespan"]
    column = (
        profile["point_column"]
        if parsed_timespan["kind"] == "point"
        else profile["range_column"]
    )
    return {
        "column": column,
        "lane": 0,
        "label": item_label(item),
        "start": parsed_timespan["start"],
        "end": parsed_timespan["end"],
        "kind": parsed_timespan["kind"],
        "fill": lighten(color, 0.2),
    }


def build_principality_items(
    items: list[dict[str, Any]], profile: dict[str, Any]
) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    local_category = profile["local_category"]

    for item in items:
        categories = item["categories"]
        primary_type = item["primary_types"][0]

        if local_category not in categories:
            continue

        if primary_type == "Gruendung":
            built.append(
                {
                    "column": profile["ruler_column"],
                    "label": f"Gruendung {local_category}",
                    "start": item["parsed_timespan"]["start"],
                    "end": item["parsed_timespan"]["end"],
                    "kind": "foundation",
                }
            )
            continue

        if primary_type == "Herrscher":
            built.append(
                {
                    "column": profile["ruler_column"],
                    "lane": 0,
                    "label": item_label(item),
                    "start": item["parsed_timespan"]["start"],
                    "end": item["parsed_timespan"]["end"],
                    "kind": "range",
                }
            )
            continue

        built.append(
            build_local_event_item(
                item,
                profile,
                PRINCIPALITY_META[profile["id"]]["color"],
            )
        )

    return built


def build_items_for_profile(
    items: list[dict[str, Any]], profile: dict[str, Any]
) -> list[dict[str, Any]]:
    if profile["type"] == "realm":
        return build_realm_items(items)
    return build_principality_items(items, profile)


def sort_key(item: dict[str, Any], column_order: list[str]) -> tuple[Any, ...]:
    order = column_order.index(item["column"])
    return (order, item.get("lane", -1), item["start"], item["label"])


def write_timeline_file(profile: dict[str, Any], timeline: dict[str, Any]) -> None:
    data_file = profile["data_file"]
    data_file.write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build timeline JSON files for the realm and principality profiles."
    )
    parser.add_argument(
        "profiles",
        nargs="*",
        help="Optional profile ids to build. Defaults to all profiles.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profiles = load_profiles()
    requested_profiles = args.profiles or list(profiles)

    unknown_profiles = [
        profile_id for profile_id in requested_profiles if profile_id not in profiles
    ]
    if unknown_profiles:
        available = ", ".join(sorted(profiles))
        unknown = ", ".join(sorted(unknown_profiles))
        raise SystemExit(
            f"Unknown profiles: {unknown}. Available profiles: {available}"
        )

    payload = load_payload()
    items = buildable_items(payload)

    built_count = 0
    for profile_id in requested_profiles:
        profile = profiles[profile_id]
        timeline = base_timeline(profile)
        timeline["items"].extend(build_items_for_profile(items, profile))
        column_order = [column["id"] for column in profile["columns"]]
        timeline["items"] = sorted(
            timeline["items"], key=lambda item: sort_key(item, column_order)
        )
        write_timeline_file(profile, timeline)
        print(f"Wrote {profile['data_file'].relative_to(REPO_ROOT)}")
        print(f"Built {len(timeline['items'])} timeline items for {profile_id}.")
        built_count += 1

    print(f"Built {built_count} timeline profile(s).")


if __name__ == "__main__":
    main()
