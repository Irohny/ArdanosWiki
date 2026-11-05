import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from wiki_dasboard.components import entry_creator, monster_creator, npc_creator
from wiki_dasboard.components.metadata import (
    build_time_metadata,
    normalize_metadata_links,
    normalize_metadata_regions,
    normalize_metadata_tags,
    metadata_display_rows,
    replace_frontmatter,
    split_frontmatter,
)


class CreatorMetadataTests(unittest.TestCase):
    def test_metadata_inputs_are_normalized_to_schema_values(self) -> None:
        self.assertEqual(
            normalize_metadata_links("Mord und Verlobung, [[Schatten der Zeit]]"),
            ["[[Mord und Verlobung]]", "[[Schatten der Zeit]]"],
        )
        self.assertEqual(
            normalize_metadata_tags("#gegenwart, drakmora #kunst"),
            ["gegenwart", "drakmora", "kunst"],
        )
        self.assertEqual(normalize_metadata_regions("Drakmora"), "Drakmora")
        self.assertEqual(
            normalize_metadata_regions("Drakmora, Mariven"),
            ["Drakmora", "Mariven"],
        )

    def test_time_text_derives_year_bounds_and_keeps_explicit_values(self) -> None:
        self.assertEqual(
            build_time_metadata("ab 2429 n.d.D.", "", ""),
            {
                "zeit_text": "ab 2429 n.d.D.",
                "zeit_von_jahr": 2429,
                "zeit_bis_jahr": None,
            },
        )
        self.assertEqual(
            build_time_metadata("2252 – 2333 n.d.D.", 2250, ""),
            {
                "zeit_text": "2252 – 2333 n.d.D.",
                "zeit_von_jahr": 2250,
                "zeit_bis_jahr": 2333,
            },
        )

    def test_frontmatter_update_preserves_body_and_merges_metadata(self) -> None:
        content = "---\ntyp: Monster\nstatus: dm\n---\n# Blaubart\n"
        updated = replace_frontmatter(content, {"status": "aktiv", "tags": ["boss"]})
        metadata, body = split_frontmatter(updated)

        self.assertEqual(metadata["typ"], "Monster")
        self.assertEqual(metadata["status"], "aktiv")
        self.assertEqual(metadata["tags"], ["boss"])
        self.assertEqual(body, "# Blaubart\n")
        self.assertIsInstance(yaml.safe_load(updated.split("---")[1]), dict)

    def test_metadata_preview_rows_are_plain_values(self) -> None:
        self.assertEqual(
            metadata_display_rows(
                {"zeit_von_jahr": 2429, "tags": ["Untot", "BOSS"], "status": "bereit"}
            ),
            [
                {"Metadatum": "Status", "Wert": "bereit"},
                {"Metadatum": "Tags", "Wert": "Untot, BOSS"},
                {"Metadatum": "Jahr von", "Wert": "2429"},
            ],
        )

    def test_npc_export_writes_metadata_and_derives_region_and_years(self) -> None:
        state = {
            "npc_creator_name": "Mira",
            "npc_creator_race": "Frei eingeben",
            "npc_creator_race_custom": "Wechselbalg",
            "npc_creator_origin": "Drakmora",
            "npc_creator_tags": "#adelig #politik",
            "npc_creator_birth_year": "2429",
            "npc_creator_metadata_status": "aktiv",
        }
        with patch.object(npc_creator.st, "session_state", state):
            exported = npc_creator._render_export_markdown()

        metadata, body = split_frontmatter(exported)
        self.assertEqual(metadata["typ"], "NPC")
        self.assertEqual(metadata["status"], "aktiv")
        self.assertEqual(metadata["region"], "Drakmora")
        self.assertEqual(metadata["tags"], ["Homebrew", "adelig", "politik"])
        self.assertEqual(metadata["zeit_von_jahr"], 2429)
        self.assertIn("**Spezies / Volk:** Wechselbalg", body)
        self.assertNotIn("**Tags:**", body)
        self.assertNotIn("Erste Erwaehnung", body)
        self.assertIn("**Herkunft:** Drakmora", body)

    def test_monster_export_writes_schema_metadata(self) -> None:
        state = {
            "monster_creator_name": "Blaubart",
            "monster_creator_campaigns": "Schatten der Zeit",
            "monster_creator_regions": "Drakmora",
            "monster_creator_metadata_tags": "#boss #untot",
            "monster_creator_time_text": "ab 2429 n.d.D.",
            "monster_creator_metadata_status": "bereit",
            "monster_creator_cr": "6",
            "monster_creator_type": "Frei eingeben",
            "monster_creator_type_custom": "#Monstrositaet",
            "monster_creator_origin": "Frei eingeben",
            "monster_creator_origin_custom": "Drakmora",
        }
        with patch.object(monster_creator.st, "session_state", state):
            exported = monster_creator._render_export_markdown()

        metadata, body = split_frontmatter(exported)
        self.assertEqual(metadata["typ"], "Monster")
        self.assertEqual(metadata["status"], "bereit")
        self.assertEqual(metadata["kampagne"], ["[[Schatten der Zeit]]"])
        self.assertEqual(metadata["region"], "Drakmora")
        self.assertEqual(metadata["tags"], ["boss", "untot"])
        self.assertEqual(metadata["zeit_von_jahr"], 2429)
        self.assertEqual(metadata["stufe"], "6")
        self.assertEqual(metadata["volk"], "#Monstrositaet")
        self.assertIn("# Blaubart", body)

    def test_monster_load_prefers_existing_frontmatter_metadata(self) -> None:
        content = (
            "---\n"
            "typ: Monster\n"
            "status: aktiv\n"
            "kampagne:\n  - '[[Schatten der Zeit]]'\n"
            "region: Drakmora\n"
            "tags: [boss]\n"
            "stufe: '6'\n"
            "volk: '#Monstrositaet'\n"
            "gesinnung: 'Neutral Gut'\n"
            "ruestungsklasse: 17\n"
            "grundlage: '#Homebrew'\n"
            "zeit_text: ab 2429 n.d.D.\n"
            "zeit_von_jahr: 2429\n"
            "---\n# Blaubart\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            monster_file = Path(directory) / "Blaubart.md"
            monster_file.write_text(content, encoding="utf-8")
            state: dict[str, object] = {}
            with (
                patch.object(monster_creator, "_bestiary_monster_file", return_value=monster_file),
                patch.object(monster_creator.st, "session_state", state),
            ):
                monster_creator._load_monster_into_state("Blaubart")

        self.assertEqual(state["monster_creator_metadata_status"], "aktiv")
        self.assertEqual(
            state["monster_creator_campaigns"], "[[Schatten der Zeit]]"
        )
        self.assertEqual(state["monster_creator_regions"], "Drakmora")
        self.assertEqual(state["monster_creator_metadata_tags"], "boss")
        self.assertEqual(state["monster_creator_cr"], "6")
        self.assertEqual(state["monster_creator_type_custom"], "#Monstrositaet")
        self.assertEqual(state["monster_creator_alignment"], "Neutral Gut")
        self.assertEqual(state["monster_creator_ac"], 17)
        self.assertEqual(state["monster_creator_foundation"], "#Homebrew")
        self.assertEqual(state["monster_creator_time_start_year"], "2429")

    def test_entry_creators_render_each_template_with_frontmatter(self) -> None:
        expected_types = {
            "Trank": "Trank",
            "Zauber": "Zauber",
            "Zutat": "Zutat",
            "Waffe": "Waffe",
            "Schatzkammer-Eintrag": "Artefakt",
        }
        for entry_kind, expected_type in expected_types.items():
            with self.subTest(entry_kind=entry_kind):
                state: dict[str, object] = {}
                with patch.object(entry_creator.st, "session_state", state):
                    entry_creator._ensure_entry_state(entry_kind)
                    state[entry_creator._state_key(entry_kind, "name")] = "Testobjekt"
                    state[entry_creator._state_key(entry_kind, "tags")] = "#test #neu"
                    if entry_kind == "Waffe":
                        state[entry_creator._state_key(entry_kind, "attunement")] = "Ja"
                    exported = entry_creator._render_entry_markdown(entry_kind)

                metadata, body = split_frontmatter(exported)
                self.assertEqual(metadata["typ"], expected_type)
                self.assertEqual(metadata["tags"], ["test", "neu"])
                self.assertIn("# Testobjekt", body)
                if entry_kind == "Waffe":
                    self.assertIs(metadata["Einstimmung"], True)
                if entry_kind == "Trank":
                    self.assertIn("- Tag: #test #neu", body)
                if entry_kind == "Zutat":
                    state = {
                        entry_creator._state_key(entry_kind, "name"): "Testkraut",
                        entry_creator._state_key(entry_kind, "description"): "Mehrzeilig\nund wirksam",
                    }
                    with patch.object(entry_creator.st, "session_state", state):
                        exported = entry_creator._render_entry_markdown(entry_kind)
                    _, body = split_frontmatter(exported)
                    self.assertIn("Mehrzeilig\nund wirksam", body)

    def test_entry_destinations_map_to_collection_or_game_master_root(self) -> None:
        for entry_kind, collection in (
            ("Trank", "Tranksammlung"),
            ("Zauber", "Zauberarchiv"),
            ("Zutat", "Zutatenarchiv"),
            ("Waffe", "Waffenkammer"),
            ("Schatzkammer-Eintrag", "Schatzkammer"),
        ):
            with self.subTest(entry_kind=entry_kind):
                state = {
                    entry_creator._state_key(entry_kind, "destination"): "Sammlung"
                }
                with patch.object(entry_creator.st, "session_state", state):
                    self.assertEqual(
                        entry_creator._destination_directory(entry_kind),
                        entry_creator.cfg.MARKDOWN_DIR / collection,
                    )
                    state[entry_creator._state_key(entry_kind, "destination")] = (
                        "Spielleiter"
                    )
                    self.assertEqual(
                        entry_creator._destination_directory(entry_kind),
                        entry_creator.cfg.MARKDOWN_DIR / "Spielleiter",
                    )


if __name__ == "__main__":
    unittest.main()