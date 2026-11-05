import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from wiki_dasboard.components.database_view import _filter_archive_visibility


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


if __name__ == "__main__":
    unittest.main()