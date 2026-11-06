import json
import unittest
from unittest.mock import patch

from wiki_dasboard.components.interactive_map import (
    MAP_LAST_CLICK_ID_KEY,
    MAP_PENDING_DIALOG_KEY,
    MAP_CONFIG_PATH,
    _accept_map_click,
    _build_map_html,
    _visible_regions,
)
from wiki_dasboard.config import cfg


class InteractiveMapTests(unittest.TestCase):
    def test_configured_regions_resolve_to_visible_wiki_pages(self) -> None:
        config = json.loads(MAP_CONFIG_PATH.read_text(encoding="utf-8"))
        regions = config["regions"]
        visible_paths = {
            str((cfg.paths.world_dir / region["page"]).resolve())
            for region in regions
        }

        visible_regions = _visible_regions(regions, visible_paths, {"Region"})

        self.assertEqual(len(visible_regions), 5)
        self.assertEqual(
            {region["name"] for region in visible_regions},
            {"Mariven", "Drakmora", "Vaylen", "Elmrath", "Schwarzklamm"},
        )
        schwarzklamm = next(
            region for region in visible_regions if region["name"] == "Schwarzklamm"
        )
        self.assertEqual(len(schwarzklamm["polygons"]), 2)

    def test_marker_coordinates_are_written_to_the_overlay(self) -> None:
        html = _build_map_html(
            "data:image/jpeg;base64,abc",
            [
                {
                    "name": "Nebelhafen",
                    "type": "Stadt",
                    "x": 49.5,
                    "y": 17,
                    "target_path": "/World/Nebelhafen.md",
                },
                {
                    "name": "Ardanos",
                    "type": "Besonderer Ort",
                    "x": 50,
                    "y": 48,
                    "target_path": "/World/Ardanos.md",
                },
                {
                    "name": "Leuchtturm",
                    "type": "Hafen",
                    "x": 12,
                    "y": 30,
                    "target_path": "/World/Leuchtturm.md",
                },
            ],
            [],
            2048,
            1536,
            {
                "Stadt": {"shape": "icon", "icon": "⚓", "color": "#123456"},
                "Besonderer Ort": {"shape": "dot", "color": "#654321"},
                "Hafen": {"shape": "icon", "icon": "✦", "color": "#135724"},
            },
        )

        self.assertIn('style="left:49.5%;top:17%;--marker-color:#123456"', html)
        self.assertIn('class="marker-icon"', html)
        self.assertIn(">⚓</span>", html)
        self.assertIn(">✦</span>", html)
        self.assertIn('style="left:12%;top:30%;--marker-color:#135724"', html)
        self.assertIn('class="marker-dot"', html)
        self.assertIn("--marker-color:#654321", html)
        self.assertIn("Nebelhafen", html)
        self.assertIn('data-target-path="/World/Nebelhafen.md"', html)
        self.assertIn('data-target-path="/World/Leuchtturm.md"', html)
        self.assertNotIn("target=\"_top\"", html)

    def test_region_renders_as_clickable_polygon(self) -> None:
        html = _build_map_html(
            "data:image/jpeg;base64,abc",
            [],
            [
                {
                    "name": "Elmrath",
                    "points": [[0, 0], [50, 0], [40, 100]],
                    "label_x": 25,
                    "label_y": 50,
                    "color": "#4f9a43",
                    "target_path": "/World/Elmrath.md",
                }
            ],
            2048,
            1536,
        )

        self.assertIn("class=\"region-area\"", html)
        self.assertIn("clip-path:polygon(0% 0%,50% 0%,40% 100%)", html)
        self.assertIn("Region Elmrath", html)
        self.assertIn('data-target-path="/World/Elmrath.md"', html)

    def test_region_renders_multiple_clickable_polygons_with_one_label(self) -> None:
        html = _build_map_html(
            "data:image/jpeg;base64,abc",
            [],
            [
                {
                    "name": "Schwarzklamm",
                    "polygons": [
                        [[10, 10], [20, 10], [20, 20]],
                        [[70, 70], [80, 70], [80, 80]],
                    ],
                    "label_x": 75,
                    "label_y": 75,
                    "color": "#805d48",
                    "target_path": "/World/Schwarzklamm.md",
                }
            ],
            2048,
            1536,
        )

        self.assertEqual(html.count('class="region-area"'), 2)
        self.assertEqual(html.count('class="region-label"'), 1)
        self.assertIn("clip-path:polygon(10% 10%,20% 10%,20% 20%)", html)
        self.assertIn("clip-path:polygon(70% 70%,80% 70%,80% 80%)", html)

    def test_map_click_is_accepted_once_only_for_visible_targets(self) -> None:
        state = {}
        click_event = {
            "click_id": "click-1",
            "target_path": "/World/Nebelhafen.md",
        }

        with patch("wiki_dasboard.components.interactive_map.st.session_state", state):
            target = _accept_map_click(click_event, {"/World/Nebelhafen.md"})
            duplicate = _accept_map_click(click_event, {"/World/Nebelhafen.md"})
            hidden_target = _accept_map_click(
                {"click_id": "click-2", "target_path": "/World/Hidden.md"},
                {"/World/Nebelhafen.md"},
            )

        self.assertEqual(target, "/World/Nebelhafen.md")
        self.assertIsNone(duplicate)
        self.assertIsNone(hidden_target)
        self.assertEqual(state[MAP_LAST_CLICK_ID_KEY], "click-2")
        self.assertEqual(state[MAP_PENDING_DIALOG_KEY], "/World/Nebelhafen.md")


if __name__ == "__main__":
    unittest.main()