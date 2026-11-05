from pathlib import Path
import unittest
from unittest.mock import patch

import wiki_dasboard.app as app
from wiki_dasboard.components import utils
from wiki_dasboard.components.npc_creator import _apply_background_preset
from wiki_dasboard.components.login import Roles, User
from wiki_dasboard.components.show_file import WIKI_DIALOG_QUERY_PARAM
from wiki_dasboard.components.toolbox import set_to_toolbox_view
from streamlit.testing.v1 import AppTest


APP_FILE = Path(__file__).resolve().parents[1] / "app.py"
LINKS_PAGE = "World/Links.md"
TASHIOREN_PAGE = "World/Gruppen/Tashioren/Tashiro'en.md"
VISHUDA_PRIVATE_PAGE = (
    "World/Gruppen/Kampange 1/Vishuda/Backstory Vishuda.md"
)
def _build_app_test() -> AppTest:
    return AppTest.from_file(str(APP_FILE))


def _build_player_app_test(character_name: str) -> AppTest:
    at = _build_app_test()
    character_ids = {
        "Gnodomir": ("gnodomir",),
        "Vishuda": ("vishuda",),
    }
    at.session_state["user"] = User(
        name=character_name,
        role=Roles.Player,
        loged_in=True,
        character_ids=character_ids.get(character_name, ()),
    )
    return at


class AppLoginGateTests(unittest.TestCase):
    def test_player_starts_with_all_public_pages_and_no_campaign_filter(self) -> None:
        at = _build_player_app_test("Gnodomir")

        at.run(timeout=30)

        visible_paths = utils.get_all_file_paths(at.session_state["tree"])
        self.assertIsNone(at.session_state["active_campaign_id"])
        self.assertIsNone(at.selectbox(key="wiki_campaign_selector").value)
        self.assertIn(str(app.cfg.paths.world_dir / "Links.md"), visible_paths)
        self.assertIn(
            str(app.cfg.paths.world_dir / "Gruppen/Gischtgeborene/Gischtgeborenen.md"),
            visible_paths,
        )
        self.assertNotIn("Seiten", [element.value for element in at.subheader])
        self.assertFalse(
            any(
                button.key and button.key.startswith("campaign-page::all::")
                for button in at.button
            )
        )
        self.assertNotIn(
            "campaign_overview_button",
            [button.key for button in at.sidebar.button],
        )
        self.assertEqual(len(at.exception), 0)

    def test_player_sees_campaign_overview_with_safe_campaign_label(self) -> None:
        at = _build_player_app_test("Gnodomir")

        at.run(timeout=30)
        at.selectbox(key="wiki_campaign_selector").set_value("schatten-der-zeit")
        at.run(timeout=30)

        visible_paths = utils.get_all_file_paths(at.session_state["tree"])
        self.assertEqual(at.session_state["active_campaign_id"], "schatten-der-zeit")
        self.assertIn(":red[Schatten der Zeit]", [element.value for element in at.title])
        self.assertNotIn("Seiten", [element.value for element in at.subheader])
        self.assertFalse(
            any(
                button.key and button.key.startswith("campaign-page::")
                for button in at.button
            )
        )
        self.assertIsNotNone(at.selectbox(key="wiki_campaign_selector"))
        self.assertIsNotNone(at.sidebar.button(key="campaign_overview_button"))
        self.assertIn(
            str(app.cfg.paths.world_dir / "Gruppen/Gischtgeborene/Gischtgeborenen.md"),
            visible_paths,
        )
        self.assertIn(
            str(app.cfg.paths.world_dir / TASHIOREN_PAGE.removeprefix("World/")),
            visible_paths,
        )
        self.assertNotIn(str(app.cfg.paths.world_dir / "Links.md"), visible_paths)
        self.assertEqual(len(at.exception), 0)

        at.sidebar.button(key="campaign_overview_button").click()
        at.run(timeout=30)

        tashioren_path = str(
            app.cfg.paths.world_dir / TASHIOREN_PAGE.removeprefix("World/")
        )
        tashioren_folder = str(app.cfg.paths.world_dir / "Gruppen/Tashioren")
        self.assertTrue(at.session_state["campaign_overview_mode"])
        self.assertIn(":red[Kampagnenübersicht]", [element.value for element in at.title])
        self.assertIsNotNone(
            at.button(key=f"campaign-overview-folder::{tashioren_folder}")
        )
        self.assertNotIn(
            f"campaign-overview::{tashioren_path}",
            [button.key for button in at.button],
        )
        self.assertEqual(len(at.exception), 0)

        at.button(key=f"campaign-overview-folder::{tashioren_folder}").click()
        at.run(timeout=30)

        self.assertIsNotNone(at.button(key=f"campaign-overview::{tashioren_path}"))

        at.button(key=f"campaign-overview-folder::{tashioren_folder}").click()
        at.run(timeout=30)

        self.assertNotIn(
            f"campaign-overview::{tashioren_path}",
            [button.key for button in at.button],
        )

        at.button(key=f"campaign-overview-folder::{tashioren_folder}").click()
        at.run(timeout=30)
        at.button(key=f"campaign-overview::{tashioren_path}").click()
        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], tashioren_path)
        self.assertNotIn("campaign_overview_mode", at.session_state)
        self.assertEqual(len(at.exception), 0)

    def test_campaign_overview_excludes_database_folders(self) -> None:
        at = _build_player_app_test("Gnodomir")

        at.run(timeout=30)
        at.selectbox(key="wiki_campaign_selector").set_value("schatten-der-zeit")
        at.run(timeout=30)

        root_path = at.session_state["root_path"]
        tree = at.session_state["tree"]
        for database in app.cfg.navigation.databases:
            database_path = str(app.cfg.paths.world_dir / database)
            document_path = str(app.cfg.paths.world_dir / database / "Overview Test.md")
            tree[root_path][database_path] = {"__files__": [document_path]}
        at.session_state["tree"] = tree

        at.sidebar.button(key="campaign_overview_button").click()
        at.run(timeout=30)

        for database in app.cfg.navigation.databases:
            database_path = str(app.cfg.paths.world_dir / database)
            document_path = str(app.cfg.paths.world_dir / database / "Overview Test.md")
            button_keys = [button.key for button in at.button]
            self.assertNotIn(f"campaign-overview-folder::{database_path}", button_keys)
            self.assertNotIn(f"campaign-overview::{document_path}", button_keys)
        self.assertEqual(len(at.exception), 0)

        at.selectbox(key="wiki_campaign_selector").set_value(None)
        at.run(timeout=30)

        self.assertIsNone(at.session_state["active_campaign_id"])
        self.assertIn(
            str(app.cfg.paths.world_dir / "Links.md"),
            utils.get_all_file_paths(at.session_state["tree"]),
        )
        self.assertEqual(len(at.exception), 0)

    def test_campaign_home_renders_default_dashboard_images(self) -> None:
        at = _build_player_app_test("Gnodomir")

        at.run(timeout=30)
        at.selectbox(key="wiki_campaign_selector").set_value("schatten-der-zeit")
        at.run(timeout=30)

        self.assertIn(":red[Schatten der Zeit]", [element.value for element in at.title])
        self.assertEqual(
            len(at.get("imgs")), len(app.cfg.layout.default_emblems) + 2
        )
        self.assertEqual(len(at.exception), 0)

    def test_vishuda_sees_character_restricted_tashioren_document(self) -> None:
        at = _build_player_app_test("Vishuda")

        at.run(timeout=30)

        self.assertIn(
            str(app.cfg.paths.world_dir / TASHIOREN_PAGE.removeprefix("World/")),
            utils.get_all_file_paths(at.session_state["tree"]),
        )
        self.assertEqual(len(at.exception), 0)

    def test_player_cannot_open_another_characters_campaign_page_by_url(self) -> None:
        at = _build_player_app_test("Gnodomir")
        denied_page = str(app.cfg.paths.repo_root / VISHUDA_PRIVATE_PAGE)
        at.query_params["page"] = denied_page

        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], at.session_state["root_path"])
        self.assertNotIn("page", at.query_params)
        self.assertNotIn(":red[Tashiro'en]", [element.value for element in at.title])
        self.assertEqual(len(at.exception), 0)

    def test_player_can_open_shared_campaign_page_by_url(self) -> None:
        at = _build_player_app_test("Gnodomir")
        shared_page = str(app.cfg.paths.repo_root / TASHIOREN_PAGE)
        at.query_params["page"] = shared_page

        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], shared_page)
        self.assertIn(":red[Tashiro'en]", [element.value for element in at.title])
        self.assertEqual(len(at.exception), 0)

    def test_player_can_open_visible_folder_through_query_parameter(self) -> None:
        at = _build_player_app_test("Gnodomir")
        visible_folder = str(app.cfg.paths.world_dir / "Gruppen/Gischtgeborene")
        at.query_params["page"] = visible_folder

        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], visible_folder)
        self.assertEqual(at.query_params["page"], [visible_folder])
        self.assertEqual(len(at.exception), 0)

    def test_player_cannot_open_bestiarium_through_query_parameter(self) -> None:
        at = _build_player_app_test("Gnodomir")
        at.query_params[utils.DATABASE_VIEW_QUERY_PARAM] = "Bestiarium"

        at.run(timeout=30)

        self.assertNotIn(utils.DATABASE_VIEW_QUERY_PARAM, at.query_params)
        self.assertFalse(at.session_state["db_flag"])
        self.assertNotIn(":red[Bestiarium]", [element.value for element in at.title])
        self.assertEqual(len(at.exception), 0)

    def test_player_cannot_open_another_characters_page_in_dialog(self) -> None:
        at = _build_player_app_test("Gnodomir")
        at.query_params[WIKI_DIALOG_QUERY_PARAM] = str(
            app.cfg.paths.repo_root / VISHUDA_PRIVATE_PAGE
        )

        at.run(timeout=30)

        self.assertNotIn(WIKI_DIALOG_QUERY_PARAM, at.query_params)
        self.assertNotIn(":red[vs_Backstory]", [element.value for element in at.title])
        self.assertEqual(len(at.exception), 0)

    def test_app_requires_login_before_navigation(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        self.assertEqual([element.label for element in at.text_input], ["Benutzername:", "Passwort"])
        self.assertEqual([element.label for element in at.button], ["Login"])
        self.assertEqual([element.value for element in at.title], ["Login"])
        self.assertEqual(len(at.sidebar.button), 0)
        self.assertEqual(len(at.selectbox), 0)

    def test_valid_login_opens_main_app(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="user_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertTrue(at.session_state["user"].loged_in)
        self.assertIn(":red[Ardanos Wiki]", [element.value for element in at.title])
        self.assertIn("Logout", [element.label for element in at.sidebar.button])

    def test_toolbox_replaces_individual_tools_in_wiki_sidebar(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="user_name").set_value("Admin")
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
        at.text_input(key="user_name").set_value("Admin")
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
        at.text_input(key="user_name").set_value("Admin")
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
        at.text_input(key="user_name").set_value("Admin")
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
        at.text_input(key="user_name").set_value("Admin")
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
        at.text_input(key="user_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], LINKS_PAGE)
        self.assertIn(":red[Links]", [element.value for element in at.title])

    def test_dialog_page_can_be_promoted_to_main_page(self) -> None:
        at = _build_app_test()
        at.run(timeout=30)
        at.text_input(key="user_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)
        current_path = at.session_state["current_path"]

        dialog_page = str(app.cfg.paths.repo_root / LINKS_PAGE)
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
        with (
            patch(
                "wiki_dasboard.app.load_auth_claims_from_cookie",
                return_value={"name": "admin-login", "role": "GameMaster"},
            ),
            patch(
                "wiki_dasboard.app.lookup_user_record",
                return_value={
                    "name": "Administration",
                    "user_name": "admin-login",
                    "role": "GameMaster",
                    "charakter": ["gnodomir"],
                },
            ),
        ):
            restored_user = app.restore_persisted_user()

        if restored_user is None:
            self.fail("Expected persisted user to be restored")

        self.assertEqual(restored_user.name, "Administration")
        self.assertEqual(restored_user.user_name, "admin-login")
        self.assertTrue(restored_user.loged_in)
        self.assertEqual(restored_user.character_ids, ("gnodomir",))


if __name__ == "__main__":
    unittest.main()