from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.add_missing_visibility import (
    FrontmatterError,
    add_missing_visibility,
    add_visibility_if_missing,
)


class AddMissingVisibilityTests(unittest.TestCase):
    def test_adds_visibility_to_frontmatter_without_changing_body(self) -> None:
        content = "---\ntyp: Beschreibung\nstatus: kanon\n---\n# Inhalt\nText\n"

        updated, result = add_visibility_if_missing(content)

        self.assertEqual(result, "added")
        self.assertEqual(
            updated,
            "---\ntyp: Beschreibung\nstatus: kanon\nsichtbarkeit: []\n---\n# Inhalt\nText\n",
        )

    def test_preserves_existing_visibility_even_when_it_is_not_empty(self) -> None:
        content = "---\ntyp: Spieler\nsichtbarkeit: [vishuda]\n---\nPrivate\n"

        updated, result = add_visibility_if_missing(content)

        self.assertEqual(result, "already-present")
        self.assertEqual(updated, content)

    def test_preserves_crlf_line_endings(self) -> None:
        content = "---\r\ntyp: Beschreibung\r\n---\r\nBody\r\n"

        updated, result = add_visibility_if_missing(content)

        self.assertEqual(result, "added")
        self.assertIn("typ: Beschreibung\r\nsichtbarkeit: []\r\n---", updated)
        self.assertNotIn("\n", updated.replace("\r\n", ""))

    def test_skips_files_without_frontmatter(self) -> None:
        content = "# Kein Frontmatter\nText\n"

        updated, result = add_visibility_if_missing(content)

        self.assertEqual(result, "no-frontmatter")
        self.assertEqual(updated, content)

    def test_invalid_yaml_fails_before_any_file_is_written(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            good = root / "a.md"
            bad = root / "b.md"
            good.write_text("---\ntyp: Beschreibung\n---\nText\n", encoding="utf-8")
            bad.write_text("---\ntyp: [broken\n---\nText\n", encoding="utf-8")

            with self.assertRaises(FrontmatterError):
                add_missing_visibility(root, apply=True)

            self.assertNotIn("sichtbarkeit", good.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()