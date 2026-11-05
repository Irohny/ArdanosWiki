import tempfile
import unittest
from pathlib import Path

from wiki_dasboard.components.file_parser import build_markdown_database, parse_markdown_file


class MarkdownDatabaseParserTests(unittest.TestCase):
    def parse_page(self, category: str, content: str) -> dict:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        path = Path(temporary_directory.name) / "Example.md"
        path.write_text(content, encoding="utf-8")
        return parse_markdown_file(path, category)

    def test_reads_bestiary_values_from_frontmatter_not_body(self) -> None:
        record = self.parse_page(
            "Bestiarium",
            "---\nstufe: '2 (450 EP)'\nvolk: '#Unhold'\n"
            "gesinnung: Rechtschaffen Böse\nruestungsklasse: 14\n"
            "grundlage: '#Homebrew'\n---\n**Stufe/Herausfordungsgrad:** 9",
        )

        self.assertEqual(record["Stufe"], "2 (450 EP)")
        self.assertEqual(record["Volk"], "#Unhold")
        self.assertEqual(record["Rüstungsklasse"], 14)

    def test_formats_structured_tags_and_components_for_database_views(self) -> None:
        record = self.parse_page(
            "Tranksammlung",
            '---\ntags: [Heilung, "Gift"]\nwert: 50G\n'
            'komponenten: ["[[Mohnblüte]]", "[[Trollharz]]"]\n'
            "seltenheit: Gewöhnlich\n---\n- Tag: #Feuer",
        )

        self.assertEqual(record["Tags"], "#Heilung #Gift")
        self.assertEqual(record["Komponenten"], "[[Mohnblüte]], [[Trollharz]]")
        self.assertEqual(record["Wert"], "50G")

    def test_includes_spell_materials_from_frontmatter(self) -> None:
        record = self.parse_page(
            "Zauberarchiv",
            "---\ngrad: 3\nschule: '#Hervorrufung'\n"
            'konzentration: Nein\nkomponenten: "#Verbal #Geste #Material"\n'
            "materialien: Schwefel\n---\n**Materialien:** Drachenblut",
        )

        self.assertEqual(record["Materialien"], "Schwefel")
        self.assertEqual(record["Konzentration"], "Nein")

    def test_reads_ingredient_fields_from_frontmatter(self) -> None:
        record = self.parse_page(
            "Zutatenarchiv",
            '---\nseltenheit: "#Selten"\nwert: 100G\n'
            'fundort: ["#Nebelwald", "#Sumpf"]\n---\n'
            "**Fundort:** #Wüste",
        )

        self.assertEqual(record["Seltenheit"], "#Selten")
        self.assertEqual(record["Wert"], "100G")
        self.assertEqual(record["Fundort"], "#Nebelwald, #Sumpf")

    def test_reads_weapon_table_fields_from_frontmatter(self) -> None:
        record = self.parse_page(
            "Waffenkammer",
            '---\ntyp: Waffe\nWaffentyp: Nahkampf\nSchadensart: Hieb\n'
            'Kategorie: Martialisch\nSeltenheit: Ungewöhnlich\nWert: 50G\n'
            'Reichweite: "1,5 m"\nEinstimmung: true\nsichtbarkeit: DM\n---\n'
            "- **Waffentyp:** Fernkampf\n- **Kategorie:** Falsch\n"
            "## Besondere Eigenschaften\n- Vielseitig\n- Magisch\n",
        )

        self.assertEqual(record["Waffentyp"], "Nahkampf")
        self.assertEqual(record["Schadensart"], "Hieb")
        self.assertEqual(record["Kategorie"], "Martialisch")
        self.assertEqual(record["Seltenheit"], "Ungewöhnlich")
        self.assertEqual(record["Wert"], "50G")
        self.assertEqual(record["Reichweite"], "1,5 m")
        self.assertIs(record["Einstimmung"], True)
        self.assertEqual(record["Sichtbarkeit"], "DM")

    def test_reads_artifact_table_fields_from_frontmatter(self) -> None:
        record = self.parse_page(
            "Schatzkammer",
            "---\ntyp: Artefakt\nseltenheit: Artefakt\neinstimmung: true\n"
            "kategorie: Waffe\nwert: Unbezahlbar\nsichtbarkeit: Alle\n---\n"
            "- **Kategorie:** Falsch\n- **Seltenheit:** Gewöhnlich\n",
        )

        self.assertEqual(record["Kategorie"], "Waffe")
        self.assertEqual(record["Seltenheit"], "Artefakt")
        self.assertIs(record["Einstimmung"], True)
        self.assertEqual(record["Wert"], "Unbezahlbar")
        self.assertEqual(record["Sichtbarkeit"], "Alle")

    def test_empty_new_archive_has_table_columns(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        archive = Path(temporary_directory.name) / "Waffenkammer"
        archive.mkdir()

        dataframe = build_markdown_database(str(archive))

        self.assertIn("Name", dataframe.columns)
        self.assertIn("Waffentyp", dataframe.columns)
        self.assertIn("Einstimmung", dataframe.columns)
        self.assertIn("Sichtbarkeit", dataframe.columns)
        self.assertEqual(len(dataframe), 0)


if __name__ == "__main__":
    unittest.main()
