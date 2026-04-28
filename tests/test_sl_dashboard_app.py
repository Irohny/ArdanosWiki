from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from sl_dashboard.app_runtime import (
    ENCOUNTER_PAGE_PATH,
    SHOW_CREATE_SESSION_EXPANDER_KEY,
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


def _build_app_test() -> AppTest:
    return AppTest.from_file(str(APP_FILE))


class SLDashboardAppTests(unittest.TestCase):
    def test_default_dashboard_renders_session_and_sidebar_controls(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        self.assertEqual(len(at.sidebar.selectbox), 0)
        self.assertEqual(at.selectbox[0].label, "Aktive Session")
        self.assertEqual(at.selectbox[0].value, "Mord und Verlobung")
        self.assertEqual(at.selectbox[0].options, ["Mord und Verlobung"])
        self.assertNotIn(
            "sl_create_session_toggle",
            [getattr(element, "key", None) for element in at.button],
        )
        self.assertIn("Mord und Verlobung", [element.value for element in at.header])
        self.assertIn(
            "Akt 1 - Markt von Tiravor", [element.value for element in at.subheader]
        )
        self.assertIn(
            "Aktuelle Szene 1 von 5",
            [element.value for element in at.caption],
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
        self.assertEqual(
            at.session_state["sl_dashboard_active_scene"],
            "Akt 1 - Markt von Tiravor",
        )

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
        link_button_labels = [
            element.label for element in getattr(at, "link_button", [])
        ]
        button_labels = [element.label for element in at.button]

        self.assertIn("Aktiv | Szene 1 von 5", [element.value for element in at.caption])
        self.assertIn(
            "Als naechstes | Szene 2 von 5",
            [element.value for element in at.caption],
        )
        self.assertNotIn("Nr", [element.value for element in at.caption])
        self.assertNotIn("Phase", [element.value for element in at.caption])
        self.assertNotIn("Ort | Status", [element.value for element in at.caption])
        self.assertIn(
            "**Moegliche Charaktere fuer Improvisation**",
            [element.value for element in at.markdown],
        )
        self.assertIn(
            "**Moegliche Orte fuer Improvisation**",
            [element.value for element in at.markdown],
        )
        self.assertIn(
            "**Thalion Gr\u00fcnquell**",
            [element.value for element in at.markdown],
        )
        self.assertIn(
            "**Hohlweg Richtung Sonnenkliff**",
            [element.value for element in at.markdown],
        )
        self.assertNotIn("Ort", [element.value for element in at.caption])
        self.assertNotIn("Hinweis", [element.value for element in at.caption])
        self.assertNotIn("NSC", [element.value for element in at.caption])
        self.assertNotIn("Details", [element.value for element in at.caption])
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
        self.assertEqual(at.selectbox[0].options, ["Mord und Verlobung"])
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

        self.assertIn("Dateiname", [element.label for element in at.text_input])
        self.assertIn("Grundlage", [element.label for element in at.text_input])
        self.assertIn("Stufe", [element.label for element in at.text_input])
        self.assertIn("Volk", [element.label for element in at.text_input])
        self.assertIn("Sprachen", [element.label for element in at.text_area])
        self.assertIn("Merkmale", [element.label for element in at.text_area])
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
        at.button(key="scene-nav-next::Akt 1 - Markt von Tiravor").click()
        at.run(timeout=30)

        self.assertEqual(
            at.session_state["sl_dashboard_active_scene"],
            "Akt 2 - Hinterhalt im Hohlweg",
        )
        self.assertIn(
            "Akt 2 - Hinterhalt im Hohlweg",
            [element.value for element in at.subheader],
        )

    def test_active_scene_query_param_sets_initial_scene(self) -> None:
        at = _build_app_test()

        at.query_params[ACTIVE_SCENE_QUERY_PARAM] = "Akt 2 - Hinterhalt im Hohlweg"
        at.run(timeout=30)

        self.assertEqual(
            at.session_state["sl_dashboard_active_scene"],
            "Akt 2 - Hinterhalt im Hohlweg",
        )
        self.assertIn(
            "Akt 2 - Hinterhalt im Hohlweg",
            [element.value for element in at.subheader],
        )
        self.assertEqual(
            at.query_params[ACTIVE_SCENE_QUERY_PARAM],
            ["Akt 2 - Hinterhalt im Hohlweg"],
        )

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
        at = _build_app_test()

        at.query_params[ACTIVE_SCENE_QUERY_PARAM] = "Akt 2 - Hinterhalt im Hohlweg"
        at.query_params[LINKED_WIKI_PAGE_QUERY_PARAM] = ELDRIC_NPC_PAGE
        at.run(timeout=30)
        at.button(key="sl-linked-page-close").click()
        at.run(timeout=30)

        self.assertNotIn(LINKED_WIKI_PAGE_QUERY_PARAM, at.query_params)
        self.assertEqual(
            at.session_state["sl_dashboard_active_scene"],
            "Akt 2 - Hinterhalt im Hohlweg",
        )


if __name__ == "__main__":
    unittest.main()