from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import sl_dashboard.editor as editor
import sl_dashboard.loader as loader


class SLDashboardEditorTests(unittest.TestCase):
    def test_add_player_combatant_to_encounter_keeps_hp_and_rk_untracked(self) -> None:
        original_editor_data_root = editor.DATA_ROOT
        original_loader_data_root = loader.DATA_ROOT
        repo_root = Path(__file__).resolve().parents[1]
        try:
            with TemporaryDirectory(dir=repo_root) as temp_dir:
                temp_path = Path(temp_dir)
                editor.DATA_ROOT = temp_path
                loader.DATA_ROOT = temp_path

                session_dir = editor.create_session(
                    title="Encounter Player Check",
                    first_scene_title="Westtor",
                )
                scene_id = editor.get_scene_id(session_dir, "westtor")

                editor.add_player_combatant_to_encounter(
                    session_dir,
                    scene_id,
                    "Alyra",
                )

                dashboard_data = loader.load_dashboard_data(session_dir=session_dir)
                combatant = dashboard_data.current_scene.encounter.runtime.combatants[0]

                self.assertEqual(combatant.name, "Alyra")
                self.assertEqual(combatant.source_type, "player")
                self.assertIsNone(combatant.max_hp)
                self.assertIsNone(combatant.current_hp)
                self.assertIsNone(combatant.initiative)
                self.assertIsNone(combatant.armor_class)
        finally:
            editor.DATA_ROOT = original_editor_data_root
            loader.DATA_ROOT = original_loader_data_root

    def test_get_bestiary_armor_class_reads_value_from_markdown(self) -> None:
        self.assertEqual(editor.get_bestiary_armor_class("Söldner"), 15)

    def test_get_bestiary_defenses_reads_values_from_markdown(self) -> None:
        defenses = editor.get_bestiary_defenses("Ser Vakor")

        self.assertEqual(defenses["immunities"], ("Feuer", "Krankheit"))
        self.assertEqual(defenses["resistances"], ("Nekrotisch", "Gift"))
        self.assertEqual(defenses["weaknesses"], ())

    def test_add_bestiary_combatant_to_encounter_is_visible_in_loader(self) -> None:
        original_editor_data_root = editor.DATA_ROOT
        original_loader_data_root = loader.DATA_ROOT
        repo_root = Path(__file__).resolve().parents[1]
        try:
            with TemporaryDirectory(dir=repo_root) as temp_dir:
                temp_path = Path(temp_dir)
                editor.DATA_ROOT = temp_path
                loader.DATA_ROOT = temp_path

                session_dir = editor.create_session(
                    title="Encounter Monster Check",
                    first_scene_title="Westtor",
                )

                editor.add_bestiary_combatant_to_encounter(
                    session_dir,
                    editor.get_scene_id(session_dir, "westtor"),
                    "Söldner",
                    max_hp=11,
                    initiative=14,
                )

                dashboard_data = loader.load_dashboard_data(session_dir=session_dir)

                self.assertIsNotNone(dashboard_data.current_scene.encounter)
                combatant = dashboard_data.current_scene.encounter.runtime.combatants[0]
                self.assertEqual(combatant.name, "Söldner")
                self.assertEqual(combatant.source_type, "bestiary")
                self.assertEqual(combatant.source_key, "Söldner")
                self.assertEqual(combatant.current_hp, 11)
                self.assertEqual(combatant.initiative, 14)
                self.assertEqual(combatant.armor_class, 15)
                self.assertEqual(
                    dashboard_data.current_scene.encounter.preparation.monster_source_keys,
                    ("Söldner",),
                )
        finally:
            editor.DATA_ROOT = original_editor_data_root
            loader.DATA_ROOT = original_loader_data_root

    def test_bestiary_combatant_loader_resolves_defenses_from_source(self) -> None:
        original_editor_data_root = editor.DATA_ROOT
        original_loader_data_root = loader.DATA_ROOT
        repo_root = Path(__file__).resolve().parents[1]
        try:
            with TemporaryDirectory(dir=repo_root) as temp_dir:
                temp_path = Path(temp_dir)
                editor.DATA_ROOT = temp_path
                loader.DATA_ROOT = temp_path

                session_dir = editor.create_session(
                    title="Encounter Monster Defense Check",
                    first_scene_title="Westtor",
                )

                editor.add_bestiary_combatant_to_encounter(
                    session_dir,
                    editor.get_scene_id(session_dir, "westtor"),
                    "Ser Vakor",
                    max_hp=99,
                    initiative=12,
                )

                dashboard_data = loader.load_dashboard_data(session_dir=session_dir)
                combatant = dashboard_data.current_scene.encounter.runtime.combatants[0]

                self.assertEqual(combatant.immunities, ("Feuer", "Krankheit"))
                self.assertEqual(combatant.resistances, ("Nekrotisch", "Gift"))
                self.assertEqual(combatant.weaknesses, ())
        finally:
            editor.DATA_ROOT = original_editor_data_root
            loader.DATA_ROOT = original_loader_data_root

    def test_update_encounter_combatant_updates_persisted_values(self) -> None:
        original_editor_data_root = editor.DATA_ROOT
        original_loader_data_root = loader.DATA_ROOT
        repo_root = Path(__file__).resolve().parents[1]
        try:
            with TemporaryDirectory(dir=repo_root) as temp_dir:
                temp_path = Path(temp_dir)
                editor.DATA_ROOT = temp_path
                loader.DATA_ROOT = temp_path

                session_dir = editor.create_session(
                    title="Encounter Edit Check",
                    first_scene_title="Westtor",
                )
                scene_id = editor.get_scene_id(session_dir, "westtor")

                editor.add_bestiary_combatant_to_encounter(
                    session_dir,
                    scene_id,
                    "Söldner",
                    max_hp=11,
                    initiative=14,
                )
                editor.update_encounter_combatant(
                    session_dir,
                    scene_id,
                    "soldner",
                    name="Veteranischer Söldner",
                    side="enemy",
                    max_hp=20,
                    current_hp=12,
                    initiative=18,
                    armor_class=16,
                )

                dashboard_data = loader.load_dashboard_data(session_dir=session_dir)
                combatant = dashboard_data.current_scene.encounter.runtime.combatants[0]

                self.assertEqual(combatant.name, "Veteranischer Söldner")
                self.assertEqual(combatant.max_hp, 20)
                self.assertEqual(combatant.current_hp, 12)
                self.assertEqual(combatant.initiative, 18)
                self.assertEqual(combatant.armor_class, 16)
        finally:
            editor.DATA_ROOT = original_editor_data_root
            loader.DATA_ROOT = original_loader_data_root

    def test_encounter_state_roundtrip_uses_separate_yaml_file(self) -> None:
        original_data_root = editor.DATA_ROOT
        try:
            with TemporaryDirectory() as temp_dir:
                editor.DATA_ROOT = Path(temp_dir)
                session_dir = editor.create_session(title="Encounter State Check")

                file_path = editor.update_encounter_state(
                    session_dir,
                    {
                        "scenes": {
                            "erste-szene": {
                                "status": "active",
                                "runtime": {
                                    "round_number": 2,
                                    "active_combatant_id": "goblin-1",
                                    "combatants": [
                                        {
                                            "id": "goblin-1",
                                            "name": "Goblin",
                                            "side": "enemy",
                                            "current_hp": 5,
                                            "max_hp": 7,
                                        }
                                    ],
                                },
                            }
                        }
                    },
                )

                self.assertEqual(file_path.name, "encounter_state.yaml")
                self.assertEqual(
                    editor.read_encounter_state(session_dir)["scenes"]["erste-szene"]["runtime"]["round_number"],
                    2,
                )
        finally:
            editor.DATA_ROOT = original_data_root

    def test_load_dashboard_data_preserves_scene_ids(self) -> None:
        original_editor_data_root = editor.DATA_ROOT
        original_loader_data_root = loader.DATA_ROOT
        repo_root = Path(__file__).resolve().parents[1]
        try:
            with TemporaryDirectory(dir=repo_root) as temp_dir:
                temp_path = Path(temp_dir)
                editor.DATA_ROOT = temp_path
                loader.DATA_ROOT = temp_path

                session_dir = editor.create_session(
                    title="Scene ID Check",
                    first_scene_title="Westtor",
                )
                editor.create_scene(
                    session_dir=session_dir,
                    title="Hinterhof",
                    location="Tiravor",
                    status="vorbereitet",
                )
                editor.update_encounter_state(
                    session_dir,
                    {
                        "scenes": {
                            "westtor": {
                                "status": "active",
                                "preparation": {
                                    "target_difficulty": "Schwer",
                                    "monster_source_keys": ["Söldner"],
                                },
                                "runtime": {
                                    "round_number": 3,
                                    "active_combatant_id": "soeldner-1",
                                    "combatants": [
                                        {
                                            "id": "soeldner-1",
                                            "name": "Söldner",
                                            "side": "enemy",
                                            "source_type": "bestiary",
                                            "source_key": "Söldner",
                                            "max_hp": 11,
                                            "current_hp": 8,
                                            "initiative": 14,
                                            "armor_class": 14,
                                            "conditions": [
                                                {
                                                    "name": "verlangsamt",
                                                    "duration": "1 Runde",
                                                }
                                            ],
                                        }
                                    ],
                                },
                                "notes": ["Verstaerkung in Runde 4."],
                            }
                        }
                    },
                )

                dashboard_data = loader.load_dashboard_data(session_dir=session_dir)

                self.assertEqual(dashboard_data.current_scene.id, "westtor")
                self.assertIsNotNone(dashboard_data.current_scene.encounter)
                self.assertEqual(dashboard_data.current_scene.encounter.scene_id, "westtor")
                self.assertEqual(dashboard_data.current_scene.encounter.runtime.round_number, 3)
                self.assertEqual(
                    dashboard_data.current_scene.encounter.runtime.combatants[0].conditions[0].name,
                    "verlangsamt",
                )
                self.assertEqual(len(dashboard_data.next_scenes), 1)
                self.assertEqual(dashboard_data.next_scenes[0].id, "hinterhof")
                self.assertIsNone(dashboard_data.next_scenes[0].encounter)
                self.assertEqual(
                    len(
                        {
                            scene.id
                            for scene in (
                                dashboard_data.current_scene,
                                *dashboard_data.next_scenes,
                            )
                        }
                    ),
                    len((dashboard_data.current_scene, *dashboard_data.next_scenes)),
                )
        finally:
            editor.DATA_ROOT = original_editor_data_root
            loader.DATA_ROOT = original_loader_data_root

    def test_create_session_writes_only_relevant_dashboard_fields(self) -> None:
        original_data_root = editor.DATA_ROOT
        try:
            with TemporaryDirectory() as temp_dir:
                editor.DATA_ROOT = Path(temp_dir)

                session_dir = editor.create_session(
                    title="Template Check",
                    in_game_date="1. Testtag",
                    region="Testregion",
                )

                content = (session_dir / "session.md").read_text(encoding="utf-8")

                self.assertIn("session_title: Template Check", content)
                self.assertIn("in_game_date: 1. Testtag", content)
                self.assertIn("region: Testregion", content)
                self.assertIn("current_scene: erste-szene", content)
                self.assertIn("scene_ids:", content)
                self.assertIn("## Aktuelles Ziel", content)
                self.assertIn("## Warnungen", content)
                self.assertNotIn("pacing:", content)
                self.assertNotIn("source_story:", content)
                self.assertNotIn("## Notizen", content)
                self.assertNotIn("## Offene Faeden", content)
        finally:
            editor.DATA_ROOT = original_data_root

    def test_create_npc_writes_template_sections_from_separate_inputs(self) -> None:
        original_data_root = editor.DATA_ROOT
        try:
            with TemporaryDirectory() as temp_dir:
                editor.DATA_ROOT = Path(temp_dir)
                session_dir = editor.create_session(title="NPC Template Check")

                npc_file = editor.create_npc(
                    session_dir=session_dir,
                    name="Testfigur",
                    title="Spionin",
                    species="Mensch",
                    origin="Tiravor",
                    description="Oeffentlich freundlich und kontrolliert.",
                    role_relationships="- [[Haus Marith]]: dient als Botin",
                    goals="Will einen Handel sabotieren.",
                    plot_hooks="- Kennt den falschen Treffpunkt der Attentaeter.",
                    secret_information="- Arbeitet heimlich fuer zwei Seiten.",
                    combat_values="- **Bestiarium-Profil:** [[Söldner]]",
                )

                content = npc_file.read_text(encoding="utf-8")

                self.assertIn("## Beschreibung und Auftreten", content)
                self.assertIn("Oeffentlich freundlich und kontrolliert.", content)
                self.assertIn("## Rolle und Beziehungen", content)
                self.assertIn("dient als Botin", content)
                self.assertIn("## Ziele", content)
                self.assertIn("Will einen Handel sabotieren.", content)
                self.assertIn("## Plot-Hooks", content)
                self.assertIn("## Geheime Informationen", content)
                self.assertIn("## Kampfwerte", content)
                self.assertIn("[[Söldner]]", content)
        finally:
            editor.DATA_ROOT = original_data_root

    def test_create_scene_writes_goal_and_scene_sections(self) -> None:
        original_data_root = editor.DATA_ROOT
        try:
            with TemporaryDirectory() as temp_dir:
                editor.DATA_ROOT = Path(temp_dir)
                session_dir = editor.create_session(title="Scene Template Check")

                scene_file = editor.create_scene(
                    session_dir=session_dir,
                    title="Hinterhof",
                    location="Tiravor",
                    status="vorbereitet",
                    atmosphere="Nasse Mauern und geduckte Stimmen.",
                    goal="Die Gruppe soll einem falschen Hinweis misstrauen.",
                    summary="Ein enger Hinterhof mit nur einem Fluchtweg.",
                    pressure="Wachen naehern sich.",
                )

                content = scene_file.read_text(encoding="utf-8")

                self.assertIn("## Atmosphäre", content)
                self.assertIn("Nasse Mauern und geduckte Stimmen.", content)
                self.assertIn("## Ziel", content)
                self.assertIn(
                    "Die Gruppe soll einem falschen Hinweis misstrauen.",
                    content,
                )
                self.assertIn("## Szenenbild", content)
                self.assertIn("Ein enger Hinterhof mit nur einem Fluchtweg.", content)
        finally:
            editor.DATA_ROOT = original_data_root

    def test_monster_links_use_species_as_hint(self) -> None:
        world_record = loader._load_world_record("World/Bestiarium/Blutjäger.md")

        link = loader._build_link(
            {
                "context": "Monster",
                "title": "Blutjäger",
                "source_file": "World/Bestiarium/Blutjäger.md",
            }
        )

        self.assertEqual(link.reason, world_record.properties.get("volk", ""))


if __name__ == "__main__":
    unittest.main()