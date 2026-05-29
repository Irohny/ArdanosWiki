from pathlib import Path
from types import SimpleNamespace
import unittest

from streamlit.testing.v1 import AppTest

from sl_dashboard.app_runtime import (
    ENCOUNTER_PAGE_PATH,
    SHOW_CREATE_SESSION_EXPANDER_KEY,
    User,
    WORKSHOP_PAGE_PATH,
)
from sl_dashboard.components.markdown import (
    ACTIVE_SCENE_QUERY_PARAM,
    LINKED_WIKI_PAGE_QUERY_PARAM,
)


APP_FILE = Path(__file__).resolve().parents[1] / "sl_dashboard_app.py"
ELDRIC_NPC_PAGE = (
    "World/Spielleiter/OneShots/Mord und Verlobung/NPCs/Eldric Feldhain.md"
)


def _logged_in_game_master() -> SimpleNamespace:
    return User(
        name="Admin",
        role=SimpleNamespace(value="GameMaster"),
        loged_in=True,
    )


def _build_app_test() -> AppTest:
    at = AppTest.from_file(str(APP_FILE))
    at.session_state["user"] = _logged_in_game_master()
    return at


def _build_logged_out_app_test() -> AppTest:
    return AppTest.from_file(str(APP_FILE))


class SLDashboardAppTests(unittest.TestCase):
    def test_default_dashboard_requires_login(self) -> None:
        at = _build_logged_out_app_test()

        at.run(timeout=30)

        self.assertEqual([element.label for element in at.text_input], ["Charaktername:", "Passwort"])
        self.assertEqual([element.label for element in at.button], ["Login"])
        self.assertEqual([element.value for element in at.title], ["Login"])
        self.assertEqual(len(at.selectbox), 0)
        self.assertEqual(len(at.sidebar.selectbox), 0)

    def test_default_dashboard_renders_session_and_sidebar_controls(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        selected_session = at.selectbox[0].value
        self.assertEqual(len(at.sidebar.selectbox), 0)
        self.assertEqual(at.selectbox[0].label, "Aktive Session")
        self.assertIn(selected_session, at.selectbox[0].options)
        self.assertGreaterEqual(len(at.selectbox[0].options), 1)
        self.assertNotIn(
            "sl_create_session_toggle",
            [getattr(element, "key", None) for element in at.button],
        )
        self.assertIn(selected_session, [element.value for element in at.header])
        self.assertIn(
            at.session_state["sl_dashboard_active_scene"],
            [element.value for element in at.subheader],
        )
        self.assertTrue(
            any(
                element.value.startswith("Aktuelle Szene ")
                for element in at.caption
            )
        )
        self.assertEqual(len(at.radio), 0)
        self.assertNotIn("**Szenenfolge**", [element.value for element in at.markdown])
        self.assertNotIn("**Pacing:**", [element.value for element in at.markdown])
        self.assertNotIn("**Offene Faeden**", [element.value for element in at.markdown])
        self.assertNotIn(
            "Noch keine offenen Faeden notiert.",
            [element.value for element in at.caption],
        )
        self.assertNotIn("Encounter", [element.label for element in at.tabs])
        self.assertNotIn("Encounter anlegen", [element.label for element in at.button])
        self.assertTrue(at.session_state["sl_dashboard_active_scene"])

    def test_switch_page_renders_kampftracker_view(self) -> None:
        at = _build_app_test()

        at.switch_page(ENCOUNTER_PAGE_PATH)
        at.run(timeout=30)

        self.assertEqual(len(at.sidebar.selectbox), 0)
        self.assertEqual(at.selectbox[0].label, "Aktive Session")
        self.assertIn("Combat laden", [element.label for element in at.selectbox])
        self.assertNotIn("Aktiver Combatant", [element.label for element in at.selectbox])
        self.assertIn("Kampftracker", [element.value for element in at.subheader])
        button_labels = [element.label for element in at.button]
        self.assertTrue(
            "Encounter anlegen" in button_labels
            or {"Runde -1", "Runde +1"}.issubset(set(button_labels))
        )
        self.assertNotIn("Encounter leeren", button_labels)
        self.assertTrue(
            any(
                element.value.startswith("Szene: ") and " | Ort: " in element.value
                for element in at.caption
            )
        )

    def test_dashboard_shows_scene_tiles_and_fallback_references(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        caption_values = [element.value for element in at.caption]
        markdown_values = [element.value for element in at.markdown]
        link_button_labels = [
            element.label for element in getattr(at, "link_button", [])
        ]
        button_labels = [element.label for element in at.button]

        self.assertTrue(
            any(value.startswith("Aktiv | Szene ") for value in caption_values)
        )
        next_scene_captions = [
            value for value in caption_values if value.startswith("Als naechstes | Szene ")
        ]
        self.assertLessEqual(len(next_scene_captions), 1)
        self.assertNotIn("Nr", caption_values)
        self.assertNotIn("Phase", caption_values)
        self.assertNotIn("Ort | Status", caption_values)
        self.assertTrue(
            "**Moegliche Charaktere fuer Improvisation**" in markdown_values
            or "Noch keine NSCs verfuegbar." in caption_values
        )
        self.assertTrue(
            "**Moegliche Orte fuer Improvisation**" in markdown_values
            or "Noch keine Orte verfuegbar." in caption_values
        )
        self.assertNotIn("Ort", caption_values)
        self.assertNotIn("Hinweis", caption_values)
        self.assertNotIn("NSC", caption_values)
        self.assertNotIn("Details", caption_values)
        self.assertNotIn("Wiki", button_labels)
        self.assertNotIn("Wiki", link_button_labels)
        if link_button_labels:
            self.assertIn("->", link_button_labels)

    def test_dashboard_uses_scene_goal_expander_without_session_status_card(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        self.assertIn("Szenenbeschreibung", [element.label for element in at.expander])
        self.assertIn("Szenenziel", [element.label for element in at.expander])
        self.assertNotIn("**Sitzungsziel**", [element.value for element in at.markdown])
        self.assertNotIn("**Warnungen**", [element.value for element in at.markdown])

    def test_switch_page_renders_workshop_view(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.run(timeout=30)

        self.assertEqual(len(at.sidebar.selectbox), 0)
        self.assertEqual(at.selectbox[0].label, "Aktive Session")
        self.assertGreaterEqual(len(at.selectbox[0].options), 1)
        self.assertIn(at.selectbox[0].value, at.selectbox[0].options)
        self.assertIsNotNone(at.button(key="sl_create_session_toggle"))
        self.assertIn("Werkstatt", [element.value for element in at.subheader])
        self.assertEqual(
            at.session_state["sl_creator_active_section"],
            0,
        )
        self.assertIn("Szenen", [element.label for element in at.expander])
        self.assertIn("NSCs", [element.label for element in at.expander])
        self.assertIn("Monster", [element.label for element in at.expander])
        self.assertIn("Session bearbeiten", [element.label for element in at.expander])
        self.assertIsNotNone(at.button(key="sl_creator_edit_session_save"))
        self.assertIn(
            "Neue Sessions legst du oben ueber den Button 'Neue Session' neben der Session-Auswahl an.",
            [element.value for element in at.caption],
        )

    def test_workshop_session_edit_uses_structured_inputs(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.run(timeout=30)

        self.assertIn("Session-Name", [element.label for element in at.text_input])
        self.assertIn("Ingame-Datum", [element.label for element in at.text_input])
        self.assertIn("Region", [element.label for element in at.text_input])
        self.assertIn("Aktuelle Szene", [element.label for element in at.selectbox])
        self.assertIn("Aktuelles Ziel", [element.label for element in at.text_area])
        self.assertIn(
            "Warnungen (eine pro Zeile)",
            [element.label for element in at.text_area],
        )
        self.assertNotIn("Markdown-Inhalt", [element.label for element in at.text_area])
        self.assertIsNotNone(at.button(key="sl_creator_edit_session_save"))

    def test_workshop_scene_section_renders_create_and_edit_tools(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 1
        at.run(timeout=30)

        self.assertEqual(
            at.session_state["sl_creator_active_section"],
            1,
        )
        self.assertIn("Neu", [element.label for element in at.tabs])
        self.assertIn("Bearbeiten", [element.label for element in at.tabs])
        self.assertIn("Szenenname", [element.label for element in at.text_input])
        self.assertIn("Ziel", [element.label for element in at.text_area])

    def test_workshop_scene_edit_uses_structured_header_fields(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 1
        at.run(timeout=30)

        self.assertIsNotNone(at.text_input(key="sl_creator_edit_form::scene::id"))
        self.assertIsNotNone(at.text_input(key="sl_creator_edit_form::scene::title"))
        self.assertIsNotNone(
            at.text_input(key="sl_creator_edit_form::scene::source_file")
        )
        self.assertIsNotNone(
            at.text_input(key="sl_creator_edit_form::scene::source_heading")
        )
        self.assertIsNotNone(
            at.text_area(key="sl_creator_edit_form::scene::image_files")
        )
        self.assertIsNotNone(
            at.text_area(key="sl_creator_edit_form::scene::section::atmosphere")
        )
        self.assertIsNotNone(
            at.text_area(key="sl_creator_edit_form::scene::section::goal")
        )
        self.assertIsNotNone(
            at.text_area(key="sl_creator_edit_form::scene::section::summary")
        )
        self.assertIsNotNone(at.button(key="sl_creator_edit_save::scene"))

    def test_workshop_npc_edit_uses_structured_header_fields(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 2
        at.session_state["sl_creator_edit_select::npc"] = "Eldric Feldhain"
        at.run(timeout=30)

        text_input_labels = [element.label for element in at.text_input]
        text_area_labels = [element.label for element in at.text_area]
        button_keys = [getattr(element, "key", None) for element in at.button]

        if "sl_creator_edit_save::npc" in button_keys:
            self.assertIn("Dateiname", text_input_labels)
            self.assertIn("Grundlage", text_input_labels)
            self.assertIn("Stufe", text_input_labels)
            self.assertIn("Volk", text_input_labels)
            self.assertIn("Sprachen", text_area_labels)
            self.assertIn("Merkmale", text_area_labels)
            self.assertIsNotNone(
                at.text_area(key="sl_creator_edit_form::npc::section::description")
            )
            self.assertIsNotNone(
                at.text_area(
                    key="sl_creator_edit_form::npc::section::role_relationships"
                )
            )
            self.assertIsNotNone(
                at.text_area(key="sl_creator_edit_form::npc::section::goals")
            )
            self.assertIsNotNone(
                at.text_area(key="sl_creator_edit_form::npc::section::plot_hooks")
            )
            self.assertIsNotNone(
                at.text_area(
                    key="sl_creator_edit_form::npc::section::secret_information"
                )
            )
            self.assertIsNotNone(
                at.text_area(key="sl_creator_edit_form::npc::section::combat_values")
            )
            self.assertIsNotNone(at.button(key="sl_creator_edit_save::npc"))
            return

        self.assertIn("Name", text_input_labels)
        self.assertIn("Titel / Amt", text_input_labels)
        self.assertIn("Spezies / Volk", text_input_labels)
        self.assertIn("Herkunft", text_input_labels)
        self.assertIn("Beschreibung und Auftreten", text_area_labels)
        self.assertNotIn("sl_creator_edit_save::npc", button_keys)

    def test_workshop_npc_creation_uses_template_section_inputs(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 2
        at.run(timeout=30)

        self.assertIn(
            "Beschreibung und Auftreten",
            [element.label for element in at.text_area],
        )
        self.assertIn(
            "Rolle und Beziehungen",
            [element.label for element in at.text_area],
        )
        self.assertIn("Ziele", [element.label for element in at.text_area])
        self.assertIn("Plot-Hooks", [element.label for element in at.text_area])
        self.assertIn(
            "Geheime Informationen",
            [element.label for element in at.text_area],
        )
        self.assertIn("Kampfwerte", [element.label for element in at.text_area])

    def test_workshop_monster_edit_loads_existing_bestiary_entry_directly(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 3
        at.session_state["monster_creator_existing_monster"] = "Blutjäger"
        at.run(timeout=30)

        self.assertEqual(at.text_input(key="monster_creator_name").value, "Blutjäger")
        self.assertEqual(at.text_input(key="monster_creator_cr").value, "5")
        self.assertEqual(
            at.selectbox(key="monster_creator_foundation").value,
            "#Online",
        )
        self.assertEqual(
            at.session_state["monster_creator_loaded_monster"],
            "Blutjäger",
        )
        self.assertNotIn("Laden", [element.label for element in at.button])

    def test_workshop_combat_section_renders_bestiary_combat_inputs(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 4
        at.run(timeout=30)

        self.assertIn("Szene", [element.label for element in at.selectbox])
        self.assertIn("Seite", [element.label for element in at.selectbox])
        self.assertIn("Bestiarium-Monster", [element.label for element in at.selectbox])
        self.assertIn("Name im Combat", [element.label for element in at.text_input])
        self.assertIn("Lebenspunkte", [element.label for element in at.number_input])
        self.assertIn("Initiative", [element.label for element in at.number_input])
        self.assertIn("RK", [element.label for element in at.number_input])
        self.assertIn("Monster in Combat einbauen", [element.label for element in at.button])
        self.assertNotIn("Spielername", [element.label for element in at.text_input])

    def test_workshop_combat_player_creation_hides_non_player_fields(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state["sl_creator_active_section"] = 4
        at.session_state["sl_creator_combat_side"] = "player"
        at.run(timeout=30)

        self.assertIn("Name im Combat", [element.label for element in at.text_input])
        self.assertIn("Seite", [element.label for element in at.selectbox])
        self.assertNotIn(
            "sl_creator_combat_monster",
            [getattr(element, "key", None) for element in at.selectbox],
        )
        self.assertNotIn(
            "sl_creator_combat_hp",
            [getattr(element, "key", None) for element in at.number_input],
        )
        self.assertNotIn(
            "sl_creator_combat_initiative",
            [getattr(element, "key", None) for element in at.number_input],
        )
        self.assertNotIn(
            "sl_creator_combat_ac",
            [getattr(element, "key", None) for element in at.number_input],
        )
        self.assertIn("Spieler in Combat einbauen", [element.label for element in at.button])
        self.assertNotIn("Monster in Combat einbauen", [element.label for element in at.button])

    def test_workshop_new_session_button_opens_reduced_form(self) -> None:
        at = _build_app_test()

        at.switch_page(WORKSHOP_PAGE_PATH)
        at.session_state[SHOW_CREATE_SESSION_EXPANDER_KEY] = True
        at.run(timeout=30)

        text_input_labels = [element.label for element in at.text_input]
        text_area_labels = [element.label for element in at.text_area]
        self.assertIn("Session-Name", text_input_labels)
        self.assertIn("Ingame-Datum", text_input_labels)
        self.assertIn("Region", text_input_labels)
        self.assertNotIn("Quellgeschichte", text_input_labels)
        self.assertNotIn("Titel der ersten Szene", text_input_labels)
        self.assertNotIn("Ort der ersten Szene", text_input_labels)
        self.assertNotIn("Pacing", text_area_labels)

    def test_scene_navigation_next_updates_active_scene(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        active_scene = at.session_state["sl_dashboard_active_scene"]
        at.button(key=f"scene-nav-next::{active_scene}").click()
        at.run(timeout=30)

        self.assertTrue(at.session_state["sl_dashboard_active_scene"])
        self.assertIn(
            at.session_state["sl_dashboard_active_scene"],
            [element.value for element in at.subheader],
        )

    def test_active_scene_query_param_sets_initial_scene(self) -> None:
        probe = _build_app_test()
        probe.run(timeout=30)
        target_scene = probe.session_state["sl_dashboard_active_scene"]

        at = _build_app_test()

        at.query_params[ACTIVE_SCENE_QUERY_PARAM] = target_scene
        at.run(timeout=30)

        self.assertEqual(at.session_state["sl_dashboard_active_scene"], target_scene)
        self.assertIn(
            target_scene,
            [element.value for element in at.subheader],
        )
        self.assertEqual(at.query_params[ACTIVE_SCENE_QUERY_PARAM], [target_scene])

    def test_right_column_hides_empty_placeholders_and_view_buttons(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        self.assertNotIn(
            "Noch keine verlinkte Wiki-Seite geoeffnet.",
            [element.value for element in at.caption],
        )
        self.assertNotIn("**Sitzungsnotizen**", [element.value for element in at.markdown])
        self.assertNotIn(
            "Noch keine Sitzungsnotizen vorhanden.",
            [element.value for element in at.caption],
        )
        self.assertNotIn("Ansehen", [element.label for element in at.button])

    def test_linked_page_query_param_renders_wiki_panel(self) -> None:
        at = _build_app_test()

        at.query_params[LINKED_WIKI_PAGE_QUERY_PARAM] = ELDRIC_NPC_PAGE
        at.run(timeout=30)

        self.assertEqual(
            at.query_params[LINKED_WIKI_PAGE_QUERY_PARAM],
            [ELDRIC_NPC_PAGE],
        )
        self.assertIn(
            "**Eldric Feldhain**",
            [element.value for element in at.markdown],
        )
        self.assertIsNotNone(at.button(key="sl-linked-page-close"))

    def test_closing_linked_page_preserves_active_scene(self) -> None:
        probe = _build_app_test()
        probe.run(timeout=30)
        target_scene = probe.session_state["sl_dashboard_active_scene"]

        at = _build_app_test()

        at.query_params[ACTIVE_SCENE_QUERY_PARAM] = target_scene
        at.query_params[LINKED_WIKI_PAGE_QUERY_PARAM] = ELDRIC_NPC_PAGE
        at.run(timeout=30)
        at.button(key="sl-linked-page-close").click()
        at.run(timeout=30)

        self.assertNotIn(LINKED_WIKI_PAGE_QUERY_PARAM, at.query_params)
        self.assertEqual(at.session_state["sl_dashboard_active_scene"], target_scene)


if __name__ == "__main__":
    unittest.main()