from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def rgba(value: str, alpha: float) -> str:
    red, green, blue = hex_to_rgb(value)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def load_data(data_file: Path) -> dict:
    with data_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def year_to_y(year: float, min_year: int, pixels_per_year: float, top: int) -> float:
    return top + (year - min_year) * pixels_per_year


def rect_height(start: int, end: int, pixels_per_year: float) -> float:
    return max(18.0, (end - start + 1) * pixels_per_year)


def split_person_name(label: str) -> list[str]:
    parts = label.split()
    if len(parts) <= 1:
        return [label]
    return [parts[0], " ".join(parts[1:])]


def split_event_label(label: str) -> list[str]:
    words = label.split()
    if len(words) <= 2:
        return [label]

    midpoint = len(words) // 2
    return [" ".join(words[:midpoint]), " ".join(words[midpoint:])]


def build_label_lines(item: dict, column_meta: dict[str, dict]) -> list[str]:
    label = item["label"]
    if item["kind"] == "foundation":
        return split_event_label(label)
    if item["kind"] == "point":
        return split_event_label(label)

    if column_meta[item["column"]].get("label_mode") == "person":
        return split_person_name(label)

    return split_event_label(label)


def fit_lines(lines: list[str], max_len: int) -> list[str]:
    return [escape_xml(line) for line in lines]


def is_conflict_item(item: dict) -> bool:
    label = item["label"].lower()
    return any(keyword in label for keyword in ("krieg", "konflikt", "nebelsteppe"))


def item_stroke(item: dict) -> tuple[str, float, str | None]:
    if item["kind"] == "foundation":
        return ("#2f2822", 1.0, None)

    if is_conflict_item(item):
        return ("#5b1f1f", 1.8, "6 3")

    return ("#2f2822", 0.8, None)


def text_block(
    lines: list[str],
    x: float,
    y: float,
    css_class: str = "item-label",
    line_height: int = 11,
) -> str:
    tspans = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else str(line_height)
        tspans.append(f'<tspan x="{x:.1f}" dy="{dy}">{line}</tspan>')
    return f'<text class="{css_class}" x="{x:.1f}" y="{y:.1f}">{"".join(tspans)}</text>'


def rotated_text_block(
    lines: list[str],
    center_x: float,
    center_y: float,
    css_class: str = "item-label-dark",
) -> str:
    tspans = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else "11"
        tspans.append(f'<tspan x="0" dy="{dy}">{line}</tspan>')
    return (
        f'<text class="{css_class}" text-anchor="middle" '
        f'transform="translate({center_x:.1f} {center_y:.1f}) rotate(-90)">{"".join(tspans)}</text>'
    )


def block_text(
    item: dict,
    column_meta: dict[str, dict],
    item_x: float,
    y: float,
    item_width: float,
    height_rect: float,
    start: int,
    end: int,
) -> str:
    lines = build_label_lines(item, column_meta)
    max_len = 18 if item_width > 120 else 14
    safe_lines = fit_lines(lines, max_len)
    text_x = item_x + 6
    is_world_column = item["column"] == "world"
    default_class = "item-label-dark" if is_world_column else "item-label"
    small_class = "item-label-dark-small" if is_world_column else "item-label-small"

    if is_world_column:
        content = safe_lines[:2]
        center_x = item_x + (item_width / 2)
        center_y = y + (height_rect / 2) - 4
        return rotated_text_block(
            content, center_x, center_y, css_class="item-label-dark"
        )

    if height_rect >= 44:
        content = safe_lines[:2] + [escape_xml(f"{start}-{end}")]
        text_y = y + 12
        return text_block(content, text_x, text_y, css_class=default_class)

    if height_rect >= 28:
        text_y = y + 12
        return text_block(safe_lines[:2], text_x, text_y, css_class=default_class)

    text_y = y + 12
    return text_block(
        [safe_lines[0]], text_x, text_y, css_class=small_class, line_height=9
    )


def build_svg(data: dict) -> str:
    min_year = data["min_year"]
    max_year = data["max_year"]
    pixels_per_year = data["pixels_per_year"]
    tick_year_step = data["tick_year_step"]

    top = 130
    left = 100
    right = 40
    bottom = 60
    header_height = 42
    column_gap = 18
    lane_gap = 6
    default_column_width = 155

    columns = data["columns"]
    column_meta: dict[str, dict] = {}
    cursor_x = left
    for column in columns:
        column_width = column.get("width", default_column_width)
        lanes = column.get("lanes", 1)
        inner_width = column_width - (lane_gap * (lanes - 1))
        lane_width = inner_width / lanes
        column_meta[column["id"]] = {
            "x": cursor_x,
            "width": column_width,
            "lane_width": lane_width,
            "lanes": lanes,
            "color": column["color"],
            "label": column["label"],
        }
        cursor_x += column_width + column_gap

    chart_width = cursor_x - column_gap - left
    chart_height = math.ceil((max_year - min_year + 1) * pixels_per_year)
    width = left + chart_width + right
    height = top + chart_height + bottom

    parts: list[str] = []
    append = parts.append

    append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
    )
    append(f'<title id="title">{escape_xml(data["title"])}</title>')
    append(f'<desc id="desc">{escape_xml(data["subtitle"])}</desc>')
    append(
        "<style>"
        ".title{font:700 24px Georgia, serif;fill:#1f1a16;}"
        ".subtitle{font:400 13px Georgia, serif;fill:#5a4f45;}"
        ".axis-label{font:600 11px Arial, sans-serif;fill:#5b5248;}"
        ".year-label{font:600 10px Arial, sans-serif;fill:#6a6158;}"
        ".column-label{font:700 12px Arial, sans-serif;fill:#201b17;}"
        ".item-label{font:600 10px Arial, sans-serif;fill:#ffffff;}"
        ".item-label-small{font:600 8.5px Arial, sans-serif;fill:#ffffff;}"
        ".item-label-dark{font:600 10px Arial, sans-serif;fill:#2c241d;}"
        ".item-label-dark-small{font:600 8.5px Arial, sans-serif;fill:#2c241d;}"
        ".lane-divider{stroke:#ffffff;stroke-width:1;opacity:0.7;}"
        ".column-border{stroke:#938778;stroke-width:1.2;fill:none;}"
        ".year-grid{stroke:#d8cec0;stroke-width:1;}"
        ".era-line{stroke:#b8ab98;stroke-width:1.2;stroke-dasharray:5 4;}"
        ".point-line{stroke:#3a3129;stroke-width:1.4;}"
        "</style>"
    )
    append(f'<text class="title" x="{left}" y="42">{escape_xml(data["title"])}</text>')
    append(
        f'<text class="subtitle" x="{left}" y="66">{escape_xml(data["subtitle"])}</text>'
    )

    for era in data["eras"]:
        y = year_to_y(era["start"], min_year, pixels_per_year, top)
        era_height = rect_height(era["start"], era["end"], pixels_per_year)
        append(
            f'<rect x="{left}" y="{y:.1f}" width="{chart_width}" height="{era_height:.1f}" '
            f'fill="{era["fill"]}" opacity="0.45"/>'
        )
        append(
            f'<text class="axis-label" x="{left + 6}" y="{y + 14:.1f}">{escape_xml(era["label"])}</text>'
        )
        append(
            f'<line class="era-line" x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}"/>'
        )

    first_tick = ((min_year + tick_year_step - 1) // tick_year_step) * tick_year_step
    for year in range(first_tick, max_year + 1, tick_year_step):
        y = year_to_y(year, min_year, pixels_per_year, top)
        append(
            f'<line class="year-grid" x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}"/>'
        )
        append(
            f'<text class="year-label" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{year}</text>'
        )

    for column in columns:
        meta = column_meta[column["id"]]
        x = meta["x"]
        append(
            f'<rect x="{x}" y="{top}" width="{meta["width"]}" height="{chart_height}" '
            f'fill="{rgba(meta["color"], 0.08)}"/>'
        )
        append(
            f'<rect class="column-border" x="{x}" y="{top}" width="{meta["width"]}" height="{chart_height}"/>'
        )
        append(
            f'<rect x="{x}" y="{top - header_height}" width="{meta["width"]}" height="{header_height}" '
            f'fill="{meta["color"]}" rx="8" ry="8"/>'
        )
        append(
            f'<text class="column-label" x="{x + meta["width"] / 2:.1f}" '
            f'y="{top - 17:.1f}" text-anchor="middle">{escape_xml(meta["label"])}</text>'
        )
        for lane_index in range(1, meta["lanes"]):
            lane_x = (
                x
                + (meta["lane_width"] * lane_index)
                + (lane_gap * lane_index)
                - (lane_gap / 2)
            )
            append(
                f'<line class="lane-divider" x1="{lane_x:.1f}" y1="{top}" x2="{lane_x:.1f}" y2="{top + chart_height}"/>'
            )

    for item in data["items"]:
        meta = column_meta[item["column"]]
        lane = item.get("lane", 0)
        item_x = meta["x"] + lane * (meta["lane_width"] + lane_gap) + 4
        item_width = meta["lane_width"] - 8
        fill = item.get("fill", meta["color"])
        start = item["start"]
        end = item["end"]

        if item["kind"] == "point":
            cy = year_to_y(start, min_year, pixels_per_year, top)
            cx = item_x + item_width / 2
            size = min(10, item_width / 3)
            points = [
                (cx, cy - size),
                (cx + size, cy),
                (cx, cy + size),
                (cx - size, cy),
            ]
            points_attr = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
            append(
                f'<polygon points="{points_attr}" fill="{fill}" stroke="#2f2822" stroke-width="1"/>'
            )
            append(
                f'<line class="point-line" x1="{cx:.1f}" y1="{cy + size:.1f}" x2="{cx:.1f}" y2="{cy + size + 18:.1f}"/>'
            )
            point_lines = fit_lines(build_label_lines(item, column_meta), 16)
            append(
                text_block(
                    point_lines[:2], cx + 4, cy + size + 14, css_class="item-label-dark"
                )
            )
            continue

        if item["kind"] == "foundation":
            y = year_to_y(start, min_year, pixels_per_year, top)
            line_x1 = meta["x"] + 6
            line_x2 = meta["x"] + meta["width"] - 6
            label_width = meta["width"] - 16
            label_x = meta["x"] + 8
            append(
                f'<line x1="{line_x1:.1f}" y1="{y:.1f}" x2="{line_x2:.1f}" y2="{y:.1f}" '
                f'stroke="{fill}" stroke-width="3" stroke-dasharray="8 5"/>'
            )
            append(
                f'<rect x="{label_x:.1f}" y="{y - 15:.1f}" width="{label_width:.1f}" height="18" '
                f'fill="#fbf8f1" stroke="{fill}" stroke-width="1" rx="8" ry="8"/>'
            )
            foundation_lines = fit_lines(build_label_lines(item, column_meta), 22)
            append(
                f'<text class="item-label-dark-small" x="{label_x + 8:.1f}" y="{y - 3:.1f}">'
                f'<tspan x="{label_x + 8:.1f}" dy="0">{foundation_lines[0]}</tspan></text>'
            )
            continue

        y = year_to_y(start, min_year, pixels_per_year, top)
        height_rect = rect_height(start, end, pixels_per_year)
        stroke_color, stroke_width, dash_array = item_stroke(item)
        clip_id = re.sub(
            r"[^a-z0-9]+",
            "-",
            f'{item["column"]}-{item["label"]}-{start}-{end}'.lower(),
        ).strip("-")
        append(
            f'<clipPath id="{clip_id}"><rect x="{item_x + 2:.1f}" y="{y + 2:.1f}" '
            f'width="{item_width - 4:.1f}" height="{height_rect - 4:.1f}" rx="6" ry="6"/></clipPath>'
        )
        dash_attr = f' stroke-dasharray="{dash_array}"' if dash_array else ""
        append(
            f'<rect x="{item_x:.1f}" y="{y:.1f}" width="{item_width:.1f}" height="{height_rect:.1f}" '
            f'fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}"{dash_attr} rx="7" ry="7"/>'
        )
        append(
            f'<g clip-path="url(#{clip_id})">{block_text(item, column_meta, item_x, y, item_width, height_rect, start, end)}</g>'
        )

    append("</svg>")
    return "".join(parts)


def resolve_output_path(data: dict, output_file: Path | None = None) -> Path:
    if output_file is not None:
        return output_file

    configured_output = data.get("output_file")
    if configured_output:
        candidate = Path(configured_output)
        if candidate.is_absolute():
            return candidate
        return REPO_ROOT / candidate

    profile_id = data.get("profile_id", "timeline")
    return REPO_ROOT / "World" / "Images" / f"{profile_id}_vertical_timeline.svg"


def render_file(data_file: Path, output_file: Path | None = None) -> Path:
    data = load_data(data_file)
    svg = build_svg(data)
    resolved_output = resolve_output_path(data, output_file)
    resolved_output.write_text(svg, encoding="utf-8")
    print(f"Wrote {resolved_output}")
    return resolved_output


def collect_default_data_files() -> list[Path]:
    default_file = ROOT / "timeline_data.json"
    profile_files = sorted(
        path for path in ROOT.glob("timeline_data_*.json") if path.is_file()
    )
    if default_file.exists():
        return [default_file, *profile_files]
    return profile_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render one or more timeline JSON files to SVG."
    )
    parser.add_argument(
        "data_files",
        nargs="*",
        help="Optional timeline JSON files. Defaults to all generated timeline_data*.json files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_files = (
        [Path(value) for value in args.data_files]
        if args.data_files
        else collect_default_data_files()
    )
    if not data_files:
        raise SystemExit("No timeline JSON files found to render.")

    for data_file in data_files:
        render_file(data_file)


if __name__ == "__main__":
    main()
