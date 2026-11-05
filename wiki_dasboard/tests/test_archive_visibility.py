import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from wiki_dasboard.components.database_view import (
    _filter_archive_visibility,
    _filter_database_document_access,
)


class ArchiveVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataframe = pd.DataFrame(
            [
                {"Name": "Public", "Sichtbarkeit": "Alle"},
                {"Name": "Private", "Sichtbarkeit": "DM"},
                {"Name": "Unspecified", "Sichtbarkeit": None},
            ]
        )

    def test_players_only_see_public_entries(self) -> None:
        user = SimpleNamespace(role=SimpleNamespace(value="Player"))
        with patch("wiki_dasboard.components.database_view.st.session_state", {"user": user}):
            visible = _filter_archive_visibility(self.dataframe)

        self.assertEqual(visible["Name"].tolist(), ["Public"])

    def test_game_master_sees_all_entries(self) -> None:
        user = SimpleNamespace(role=SimpleNamespace(value="GameMaster"))
        with patch("wiki_dasboard.components.database_view.st.session_state", {"user": user}):
            visible = _filter_archive_visibility(self.dataframe)

        self.assertEqual(
            visible["Name"].tolist(), ["Public", "Private", "Unspecified"]
        )

    def test_database_rows_use_document_acl_and_active_campaign(self) -> None:
        dataframe = pd.DataFrame(
            [
                {"Name": "Gischtgeborene", "Pfad": "/world/gischt.md"},
                {"Name": "Tashioren", "Pfad": "/world/tashioren.md"},
            ]
        )
        user = SimpleNamespace(role=SimpleNamespace(value="Player"))
        with (
            patch(
                "wiki_dasboard.components.database_view.st.session_state",
                {
                    "user": user,
                    "active_campaign_id": "campaign_01",
                    "TestDB": dataframe,
                },
            ),
            patch(
                "wiki_dasboard.components.database_view.utils.has_permission",
                side_effect=lambda path, *_args, **kwargs: (
                    path.endswith("gischt.md")
                    and kwargs["campaign_id"] == "campaign_01"
                ),
            ),
        ):
            visible = _filter_database_document_access("TestDB")

        self.assertEqual(visible["Name"].tolist(), ["Gischtgeborene"])


if __name__ == "__main__":
    unittest.main()