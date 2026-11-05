import unittest
from unittest.mock import patch

import wiki_dasboard.app as app
from wiki_dasboard.components import utils
from wiki_dasboard.components.database_view import set_to_databse_view
from wiki_dasboard.config import cfg


class DatabaseNavigationTests(unittest.TestCase):
    def test_database_selection_is_stored_in_query_params(self) -> None:
        state = {}
        query_params = {}
        with (
            patch("wiki_dasboard.components.database_view.st.session_state", state),
            patch("wiki_dasboard.components.database_view.st.query_params", query_params),
        ):
            set_to_databse_view("Tranksammlung")

        self.assertEqual(query_params[utils.DATABASE_VIEW_QUERY_PARAM], "Tranksammlung")
        self.assertTrue(state["db_flag"])

    def test_main_restores_database_view_from_query_params(self) -> None:
        database = cfg.DATABASE_LIST[0]
        state = {}
        query_params = {utils.DATABASE_VIEW_QUERY_PARAM: database}
        with (
            patch("wiki_dasboard.app.st.session_state", state),
            patch("wiki_dasboard.app.st.query_params", query_params),
            patch("wiki_dasboard.app.header"),
            patch("wiki_dasboard.app.create_sidebar"),
        ):
            app.main()

        self.assertEqual(state["db"], database)
        self.assertTrue(state["db_flag"])

    def test_regular_page_navigation_clears_database_view(self) -> None:
        state = {"db_flag": True, "db": "Tranksammlung"}
        query_params = {
            utils.DATABASE_VIEW_QUERY_PARAM: "Tranksammlung",
            utils.WIKI_DIALOG_QUERY_PARAM: "/wiki/World/Linked.md",
        }
        with (
            patch("wiki_dasboard.components.utils.st.session_state", state),
            patch("wiki_dasboard.components.utils.st.query_params", query_params),
        ):
            utils.sync_current_path("/wiki/World/Links.md")

        self.assertNotIn(utils.DATABASE_VIEW_QUERY_PARAM, query_params)
        self.assertNotIn(utils.WIKI_DIALOG_QUERY_PARAM, query_params)
        self.assertEqual(query_params["page"], "/wiki/World/Links.md")
        self.assertFalse(state["db_flag"])


if __name__ == "__main__":
    unittest.main()