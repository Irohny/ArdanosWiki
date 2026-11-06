from __future__ import annotations

import base64
from html import escape
import json
import mimetypes
from pathlib import Path
import re

import streamlit as st
import streamlit.components.v1 as components

from wiki_dasboard.components import utils
from wiki_dasboard.config import cfg


ARDANOS_MAP_OPEN_KEY = "ardanos_map_open"
MAP_MARKER_TYPES_KEY = "ardanos_map_marker_types"
MAP_COMPONENT_KEY = "ardanos_interactive_map"
MAP_LAST_CLICK_ID_KEY = "ardanos_map_last_click_id"
MAP_PENDING_DIALOG_KEY = "ardanos_map_pending_dialog"
MAP_CONFIG_PATH = cfg.paths.world_dir / "Images" / "Maps" / "ardanos_markers.json"
_map_component = components.declare_component(
    "ardanos_interactive_map",
    path=str(Path(__file__).parent / "interactive_map_frontend"),
)


@st.cache_data(show_spinner=False)
def _image_data_uri(image_path: str, modified_ns: int) -> str:
    path = Path(image_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _visible_markers(
    markers: list[dict], visible_paths: set[str], selected_types: set[str]
) -> list[dict]:
    visible: list[dict] = []
    world_root = cfg.paths.world_dir.resolve()
    for marker in markers:
        if marker.get("type") not in selected_types:
            continue
        try:
            x = float(marker["x"])
            y = float(marker["y"])
            target_path = (world_root / str(marker["page"])).resolve()
            target_path.relative_to(world_root)
        except (KeyError, TypeError, ValueError):
            continue
        if not (0 <= x <= 100 and 0 <= y <= 100):
            continue
        if str(target_path) not in visible_paths:
            continue
        visible.append({**marker, "x": x, "y": y, "target_path": str(target_path)})
    return visible


def _visible_regions(
  regions: list[dict], visible_paths: set[str], selected_types: set[str]
) -> list[dict]:
    visible: list[dict] = []
    world_root = cfg.paths.world_dir.resolve()
    for region in regions:
        if region.get("type", "Region") not in selected_types:
            continue
        try:
            raw_polygons = region.get("polygons")
            if raw_polygons is None:
                raw_polygons = [region["points"]]
            polygons = [
                [[float(point[0]), float(point[1])] for point in polygon]
                for polygon in raw_polygons
            ]
            label_x = float(region["label_x"])
            label_y = float(region["label_y"])
            target_path = (world_root / str(region["page"])).resolve()
            target_path.relative_to(world_root)
        except (IndexError, KeyError, TypeError, ValueError):
            continue
        if not polygons or any(
            len(polygon) < 3
            or any(
                not (0 <= coordinate <= 100)
                for point in polygon
                for coordinate in point
            )
            for polygon in polygons
        ):
            continue
        if not (0 <= label_x <= 100 and 0 <= label_y <= 100):
            continue
        if str(target_path) not in visible_paths:
            continue
        color = str(region.get("color", "#527b68"))
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            color = "#527b68"
        visible.append(
            {
                **region,
                "polygons": polygons,
                "label_x": label_x,
                "label_y": label_y,
                "color": color,
                "target_path": str(target_path),
            }
        )
    return visible


def _accept_map_click(click_event: object, visible_targets: set[str]) -> str | None:
    if not isinstance(click_event, dict):
        return None

    click_id = str(click_event.get("click_id", "")).strip()
    target_path = str(click_event.get("target_path", "")).strip()
    if not click_id or click_id == st.session_state.get(MAP_LAST_CLICK_ID_KEY):
        return None

    st.session_state[MAP_LAST_CLICK_ID_KEY] = click_id
    if target_path not in visible_targets:
        return None

    st.session_state[MAP_PENDING_DIALOG_KEY] = target_path
    return target_path


def _build_map_html(
    image_uri: str,
    markers: list[dict],
    regions: list[dict],
    image_width: int,
    image_height: int,
    marker_type_settings: dict[str, dict] | None = None,
) -> str:
    marker_elements = []
    region_elements = []
    region_label_elements = []
    marker_type_settings = marker_type_settings or {}
    for region in regions:
        name = escape(str(region["name"]))
        polygons = region.get("polygons", [region.get("points", [])])
        position = "left:{:g}%;top:{:g}%".format(
            region["label_x"], region["label_y"]
        )
        for polygon in polygons:
            points = ",".join(
                "{:g}% {:g}%".format(x, y) for x, y in polygon
            )
            region_elements.append(
                f'<button type="button" class="region-area" '
                f'data-target-path="{escape(str(region["target_path"]), quote=True)}" '
                f'style="clip-path:polygon({points});'
                f'background-color:{region["color"]}88" '
                f'aria-label="Region {name}" title="{name}"></button>'
            )
        region_label_elements.append(
            f'<span class="region-label" style="{position}">{name}</span>'
        )

    for marker in markers:
        name = escape(str(marker["name"]))
        marker_type = str(marker["type"])
        marker_settings = marker_type_settings.get(marker_type, {})
        if not isinstance(marker_settings, dict):
            marker_settings = {}
        marker_color = str(marker_settings.get("color", "#d29d2e"))
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", marker_color):
            marker_color = "#d29d2e"
        position = "left:{:g}%;top:{:g}%".format(marker["x"], marker["y"])
        marker_shape = marker_settings.get("shape", "icon")
        if marker_shape == "dot":
            marker_symbol = '<span class="marker-dot" aria-hidden="true"></span>'
        else:
            icon = escape(str(marker_settings.get("icon", "•")))
            marker_symbol = (
                f'<span class="marker-icon" aria-hidden="true">{icon}</span>'
            )
        marker_elements.append(
            f'<button type="button" class="marker" '
            f'data-target-path="{escape(str(marker["target_path"]), quote=True)}" '
            f'style="{position};--marker-color:{marker_color}" '
            f'aria-label="{name} ({escape(marker_type)})" title="{name}">'
            f'{marker_symbol}<span class="marker-label">{name}</span></button>'
        )

    return f"""
<style>
.ardanos-map, .ardanos-map * {{ box-sizing: border-box; }}
.ardanos-map {{ width: 100%; max-width: 1280px; margin: 0 auto; color: #24231f; }}
.ardanos-map__viewport {{ width: 100%; aspect-ratio: {image_width} / {image_height};
  overflow: auto; background: #d7e0dd; border: 1px solid #a6a092; }}
.ardanos-map__canvas {{ position: relative; width: 100%;
  aspect-ratio: {image_width} / {image_height}; }}
.ardanos-map__canvas img {{ display: block; width: 100%; height: 100%; object-fit: fill; }}
.ardanos-map__region-layer, .ardanos-map__marker-layer {{ position: absolute; inset: 0; }}
.ardanos-map__region-layer {{ z-index: 1; }}
.ardanos-map .region-area {{ position: absolute; inset: 0; display: block;
    width: 100%; padding: 0; border: 0; cursor: pointer;
  opacity: .60; filter: drop-shadow(0 0 3px #171a18); transition: opacity 120ms ease; }}
.ardanos-map .region-area:hover, .ardanos-map .region-area:focus-visible {{ opacity: .78; }}
.ardanos-map .region-area:focus-visible {{ outline: 2px solid #fff; }}
.ardanos-map .region-label {{ position: absolute; display: block; transform: translate(-50%, -50%);
  padding: 3px 7px; border-radius: 3px; background: #171a18a8; color: #fff;
  font: 700 14px/1.2 Georgia, serif; text-shadow: 0 1px 2px #000; white-space: nowrap;
  pointer-events: none; z-index: 3; }}
.ardanos-map__marker-layer {{ position: absolute; inset: 0; }}
.ardanos-map .marker {{ position: absolute; display: flex; align-items: center; gap: 5px;
    padding: 0; border: 0; background: transparent; cursor: pointer;
    transform: translate(-50%, -50%); color: #161a18; z-index: 2; }}
.ardanos-map .marker-dot {{ width: 19px; height: 19px; border: 2px solid #fff;
    border-radius: 50%; background: var(--marker-color, #d29d2e);
    box-shadow: 0 1px 5px #1119; flex: 0 0 19px; }}
.ardanos-map .marker-icon {{ display: grid; place-items: center; width: 26px; height: 26px;
  flex: 0 0 26px; border: 1px solid #fff; border-radius: 50%; background: #fffdf2;
    color: var(--marker-color, #d29d2e); box-shadow: 0 1px 5px #1119;
    font: 21px/1 "Apple Color Emoji", "Segoe UI Emoji", sans-serif; }}
.ardanos-map .marker-label {{ opacity: 0; padding: 3px 6px; border-radius: 3px;
  background: #fffdf2ee; box-shadow: 0 1px 5px #1115; font: 600 12px/1.2 sans-serif;
  white-space: nowrap; transition: opacity 100ms ease; }}
.ardanos-map .marker:hover, .ardanos-map .marker:focus-visible {{ z-index: 4; }}
.ardanos-map .marker:hover .marker-label,
.ardanos-map .marker:focus-visible .marker-label {{ opacity: 1; }}
.ardanos-map .marker:focus-visible {{ outline: 2px solid #182c26; outline-offset: 3px; }}
</style>
<div class="ardanos-map">
  <div class="ardanos-map__viewport">
    <div class="ardanos-map__canvas">
      <img src="{image_uri}" alt="Karte von Ardanos">
      <div class="ardanos-map__region-layer">{"".join(region_elements)}{"".join(region_label_elements)}</div>
      <div class="ardanos-map__marker-layer">{"".join(marker_elements)}</div>
    </div>
  </div>
</div>
"""


def render_interactive_map() -> None:
    try:
        config = json.loads(MAP_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        st.error(f"Kartenkonfiguration konnte nicht geladen werden: {error}")
        return

    markers = config.get("markers", [])
    regions = config.get("regions", [])
    marker_types = list(
      dict.fromkeys(
        [str(region.get("type", "Region")) for region in regions]
        + [str(marker.get("type", "")) for marker in markers]
      )
    )
    selected_types = st.pills(
        "Marker anzeigen",
        options=marker_types,
        selection_mode="multi",
        default=marker_types,
        key=MAP_MARKER_TYPES_KEY,
    )
    visible_paths = {
        str(Path(path).resolve())
        for path in utils.get_all_file_paths(st.session_state["tree"])
    }
    selected_types = set(selected_types or [])
    visible_markers = _visible_markers(markers, visible_paths, selected_types)
    visible_regions = _visible_regions(regions, visible_paths, selected_types)
    if not visible_markers and not visible_regions:
        st.info("Für die ausgewählten Markertypen sind keine sichtbaren Ziele vorhanden.")

    st.markdown(
        """
        <style>
        .st-key-ardanos_interactive_map { display: block !important; }
        .st-key-ardanos_interactive_map iframe { min-height: 1px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    image_path = (cfg.paths.repo_root / str(config.get("image", ""))).resolve()
    if not image_path.is_file():
        st.error(f"Kartenbild nicht gefunden: {image_path}")
        return
    image_uri = _image_data_uri(str(image_path), image_path.stat().st_mtime_ns)
    map_html = _build_map_html(
        image_uri,
        visible_markers,
        visible_regions,
        int(config.get("image_width", 4)),
        int(config.get("image_height", 3)),
        config.get("marker_types", {}),
    )
    click_event = _map_component(
        map_html=map_html,
        key=MAP_COMPONENT_KEY,
        default=None,
    )
    visible_targets = {
        item["target_path"] for item in visible_markers + visible_regions
    }
    if _accept_map_click(click_event, visible_targets):
        st.rerun()