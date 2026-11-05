from pathlib import Path
import unittest
from unittest.mock import patch

import wiki_dasboard.app as app
from wiki_dasboard.components import utils
from wiki_dasboard.components.npc_creator import _apply_background_preset
from wiki_dasboard.components.show_file import WIKI_DIALOG_QUERY_PARAM
from wiki_dasboard.components.toolbox import set_to_toolbox_view
from streamlit.testing.v1 import AppTest


APP_FILE = Path(__file__).resolve().parents[1] / "app.py"
LINKS_PAGE = "World/Links.md"


def _build_app_test() -> AppTest:
    return AppTest.from_file(str(APP_FILE))


class AppLoginGateTests(unittest.TestCase):
    def test_app_requires_login_before_navigation(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        self.assertEqual([element.label for element in at.text_input], ["Charaktername:", "Passwort"])
        self.assertEqual([element.label for element in at.button], ["Login"])
        self.assertEqual([element.value for element in at.title], ["Login"])
        self.assertEqual(len(at.sidebar.button), 0)
        self.assertEqual(len(at.selectbox), 0)

    def test_valid_login_opens_main_app(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertTrue(at.session_state["user"].loged_in)
        self.assertIn(":red[Ardanos Wiki]", [element.value for element in at.title])
        self.assertIn("Logout", [element.label for element in at.sidebar.button])

    def test_toolbox_replaces_individual_tools_in_wiki_sidebar(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        sidebar_labels = [element.label for element in at.sidebar.button]
        self.assertIn("🛠️ Toolbox", sidebar_labels)
        self.assertNotIn("🛠️ Encounter Rechner", sidebar_labels)
        self.assertNotIn("🛠️ NSC Ersteller", sidebar_labels)
        self.assertNotIn("🛠️ Monster Ersteller", sidebar_labels)

        at.sidebar.button(key="Toolbox_view").click()
        at.run(timeout=30)

        self.assertIn(":red[Toolbox]", [element.value for element in at.title])
        self.assertNotIn("Toolbox", [element.value for element in at.subheader])
        self.assertIn("Werkzeug", [element.label for element in at.button_group])
        tool_options = [
            option.content
            for option in at.button_group(key="toolbox_selected_tool").options
        ]
        self.assertIn("NSC Ersteller", tool_options)
        self.assertIn("Trank", tool_options)
        self.assertIn("Zauber", tool_options)
        self.assertIn("Zutat", tool_options)
        self.assertIn("Waffe", tool_options)
        self.assertIn("Schatzkammer-Eintrag", tool_options)
        self.assertEqual(len(at.exception), 0)

    def test_toolbox_can_be_opened_from_a_wiki_page(self) -> None:
        at = _build_app_test()
        at.query_params["page"] = LINKS_PAGE

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertIn("Toolbox_view", [button.key for button in at.sidebar.button])
        at.sidebar.button(key="Toolbox_view").click()
        at.run(timeout=30)

        self.assertIn(":red[Toolbox]", [element.value for element in at.title])
        self.assertNotIn("Toolbox", [element.value for element in at.subheader])
        self.assertIsNotNone(at.button_group(key="toolbox_selected_tool"))
        self.assertEqual(len(at.exception), 0)

    def test_opening_toolbox_clears_stale_navigation_query_params(self) -> None:
        state = {}
        query_params = {
            utils.DATABASE_VIEW_QUERY_PARAM: "Tranksammlung",
            WIKI_DIALOG_QUERY_PARAM: "/wiki/World/Links.md",
        }

        with (
            patch("wiki_dasboard.components.toolbox.st.session_state", state),
            patch("wiki_dasboard.components.toolbox.st.query_params", query_params),
        ):
            set_to_toolbox_view()

        self.assertEqual(state["db"], "Toolbox")
        self.assertTrue(state["db_flag"])
        self.assertEqual(query_params, {})

    def test_npc_creator_fields_and_role_selection_remain_visible(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)
        at.session_state["toolbox_selected_tool"] = "NSC Ersteller"
        at.sidebar.button(key="Toolbox_view").click()
        at.run(timeout=30)

        self.assertIsNotNone(at.text_input(key="npc_creator_metadata_status"))
        self.assertIsNotNone(at.text_input(key="npc_creator_alias"))
        self.assertIsNotNone(at.text_area(key="npc_creator_role_relations"))
        self.assertNotIn(
            "npc_creator_enable_profile_module",
            [element.key for element in at.checkbox],
        )
        self.assertEqual(len(at.exception), 0)

    def test_npc_role_preset_updates_background(self) -> None:
        state = {"npc_creator_role_preset": "Krieger"}
        with patch("wiki_dasboard.components.npc_creator.st.session_state", state):
            _apply_background_preset()

        self.assertIn("Veteran vieler Kaempfe", state["npc_creator_background"])

    def test_trank_creator_renders_inside_toolbox(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)
        at.session_state["toolbox_selected_tool"] = "Trank"
        at.sidebar.button(key="Toolbox_view").click()
        at.run(timeout=30)

        self.assertIn("Trank erstellen", [element.value for element in at.subheader])
        self.assertIsNotNone(at.text_input(key="entry_creator_trank_name"))
        self.assertIsNotNone(at.text_input(key="entry_creator_trank_components"))
        self.assertIsNotNone(at.selectbox(key="entry_creator_trank_destination"))
        self.assertEqual(len(at.exception), 0)

    def test_logout_returns_to_login_screen(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        logout = next(button for button in at.sidebar.button if button.label == "Logout")
        logout.click()
        at.run(timeout=30)

        self.assertFalse(at.session_state["user"].loged_in)
        self.assertEqual([element.value for element in at.title], ["Login"])
        self.assertEqual(len(at.exception), 0)

    def test_page_query_param_survives_login(self) -> None:
        at = _build_app_test()

        at.query_params["page"] = LINKS_PAGE
        at.run(timeout=30)

        self.assertEqual(at.query_params["page"], [LINKS_PAGE])
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], LINKS_PAGE)
        self.assertIn(":red[Links]", [element.value for element in at.title])

    def test_dialog_page_can_be_promoted_to_main_page(self) -> None:
        at = _build_app_test()
        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)
        current_path = at.session_state["current_path"]

        dialog_page = str(app.cfg.REPO_ROOT / LINKS_PAGE)
        at.query_params[WIKI_DIALOG_QUERY_PARAM] = dialog_page
        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], current_path)
        self.assertIsNotNone(at.button(key="open_dialog_page_as_new_main_page"))

        at.button(key="open_dialog_page_as_new_main_page").click()
        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], dialog_page)
        self.assertEqual(at.query_params["page"], [dialog_page])
        self.assertNotIn(WIKI_DIALOG_QUERY_PARAM, at.query_params)
        self.assertIn(":red[Links]", [element.value for element in at.title])

    def test_cookie_claims_restore_logged_in_user(self) -> None:
        with patch("wiki_dasboard.app.load_auth_claims_from_cookie", return_value={"name": "Admin", "role": "GameMaster"}):
            restored_user = app.restore_persisted_user()

        self.assertIsNotNone(restored_user)
        self.assertEqual(restored_user.name, "Admin")
        self.assertTrue(restored_user.loged_in)


if __name__ == "__main__":
    unittest.main()