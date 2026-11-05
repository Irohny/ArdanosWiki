import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import streamlit as st

from wiki_dasboard.components import utils
from wiki_dasboard.components.header import header
from wiki_dasboard.config import cfg


REPO_ROOT = cfg.paths.repo_root
WORLD_ROOT = REPO_ROOT / "World"
TIMELINE_NAMES = (
    "ardanos",
    "drakmora",
    "elmrath",
    "mariven",
    "schwarzklamm",
    "vaylen",
)


class DashboardTimelineAssetTests(unittest.TestCase):
    def test_all_timeline_assets_are_resolvable_and_indexed_for_wiki_images(self) -> None:
        self.assertEqual(utils.validate_dashboard_views(), [])
        images = utils.collect_images_by_name(
            str(cfg.paths.repo_root / cfg.paths.image_dir)
        )

        for name in TIMELINE_NAMES:
            with self.subTest(timeline=name):
                filename = f"{name}_vertical_timeline.svg"
                self.assertIn(filename, images)
                self.assertTrue(Path(images[filename]).is_file())

    def test_timeline_folder_routes_select_their_dashboard_views(self) -> None:
        st.session_state["root_path"] = str(WORLD_ROOT)

        for view in cfg.layout.views:
            with self.subTest(view=view.key):
                folder = WORLD_ROOT / view.path_prefix
                self.assertEqual(utils.resolve_dashboard_view(str(folder)), view)

    def test_campaign_context_renders_each_configured_dashboard_view(self) -> None:
        for view in cfg.layout.views:
            with self.subTest(view=view.key):
                state = {
                    "user": SimpleNamespace(
                        role=SimpleNamespace(value="Player")
                    ),
                    "active_campaign_id": "campaign_01",
                    "current_path": str(WORLD_ROOT / view.path_prefix),
                    "root_path": str(WORLD_ROOT),
                    "db_flag": False,
                }
                with (
                    patch(
                        "wiki_dasboard.components.header.st.session_state",
                        state,
                    ),
                    patch(
                        "wiki_dasboard.components.header.st.columns",
                        return_value=[Mock(), Mock()],
                    ),
                    patch("wiki_dasboard.components.header.apply_breadcrumb_styles"),
                    patch("wiki_dasboard.components.header.render_breadcrumbs"),
                    patch("wiki_dasboard.components.header.__search_field"),
                    patch("wiki_dasboard.components.header.show_image"),
                    patch(
                        "wiki_dasboard.components.header.render_dashboard"
                    ) as render_dashboard,
                    patch(
                        "wiki_dasboard.components.header.st.title"
                    ),
                ):
                    header()

                render_dashboard.assert_called_once_with(view)


if __name__ == "__main__":
    unittest.main()