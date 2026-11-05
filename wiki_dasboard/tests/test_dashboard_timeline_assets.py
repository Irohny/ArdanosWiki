import unittest
from pathlib import Path

import streamlit as st

from wiki_dasboard.components import utils
from wiki_dasboard.config import cfg


REPO_ROOT = cfg.REPO_ROOT
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
        images = utils.collect_images_by_name(str(cfg.REPO_ROOT / cfg.IMAGE_DIR))

        for name in TIMELINE_NAMES:
            with self.subTest(timeline=name):
                filename = f"{name}_vertical_timeline.svg"
                self.assertIn(filename, images)
                self.assertTrue(Path(images[filename]).is_file())

    def test_timeline_folder_routes_select_their_dashboard_views(self) -> None:
        st.session_state["root_path"] = str(WORLD_ROOT)

        for view in cfg.DASHBOARD_VIEWS:
            with self.subTest(view=view.key):
                folder = WORLD_ROOT / view.path_prefix
                self.assertEqual(utils.resolve_dashboard_view(str(folder)), view)


if __name__ == "__main__":
    unittest.main()