from pathlib import Path
import unittest

from wiki_dasboard.components.metadata import split_frontmatter
from wiki_dasboard.config import cfg
from utils.migrate_player_acl import migrate_document_text


class AclMetadataMigrationTests(unittest.TestCase):
    def test_unclassified_file_becomes_explicitly_public_and_keeps_body(self) -> None:
        content = "---\ntyp: Beschreibung\nstatus: kanon\n---\n## Ziele\nSecret\n"

        migrated, disposition = migrate_document_text(
            content, Path("Beschreibung.md"), {}
        )
        metadata, body = split_frontmatter(migrated)

        self.assertEqual(metadata["sichtbarkeit"], [])
        self.assertEqual(metadata["abschnitt_sichtbarkeit"], {"Ziele": []})
        self.assertEqual(body, split_frontmatter(content)[1])
        self.assertEqual(disposition, "public")

    def test_legacy_prefix_becomes_character_id_grant(self) -> None:
        content = "---\ntyp: Spieler\n---\nPrivate\n"

        migrated, disposition = migrate_document_text(
            content,
            Path("gn_Gnodomir/Backstory.md"),
            {},
        )
        metadata, _ = split_frontmatter(migrated)

        self.assertEqual(metadata["sichtbarkeit"], ["gnodomir"])
        self.assertEqual(disposition, "character")

    def test_secret_information_uses_document_grant_instead_of_gm_only_rule(self) -> None:
        content = "---\ntyp: NPC\n---\n## Geheime Informationen\nDetails\n"

        migrated, _ = migrate_document_text(content, Path("NPC.md"), {})
        metadata, _ = split_frontmatter(migrated)

        self.assertNotIn("Geheime Informationen", metadata.get("abschnitt_sichtbarkeit", {}))

    def test_campaign_acl_becomes_explicit_ids_and_section_acl_is_separate(self) -> None:
        content = (
            "---\n"
            "kampagne: ['[[Schatten der Zeit]]']\n"
            "sichtbarkeit:\n"
            "  datei: kampagne\n"
            "  abschnitte:\n"
            "    'Geheime Details': [vishuda]\n"
            "---\n"
            "## Geheime Details\nDetails\n"
        )

        migrated, disposition = migrate_document_text(
            content,
            Path("Tashioren.md"),
            {
                cfg.player_access.campaign_aliases["Schatten der Zeit"]: {
                    "gnodomir",
                    "vishuda",
                }
            },
        )
        metadata, _ = split_frontmatter(migrated)

        self.assertEqual(metadata["sichtbarkeit"], ["gnodomir", "vishuda"])
        self.assertEqual(
            metadata["abschnitt_sichtbarkeit"],
            {"Geheime Details": ["vishuda"]},
        )
        self.assertNotIn("abschnitte", metadata["sichtbarkeit"])
        self.assertEqual(disposition, "character")

    def test_dm_archive_visibility_preserves_workflow_status(self) -> None:
        content = (
            "---\n"
            "typ: Waffe\n"
            "status: vorbereitet\n"
            "sichtbarkeit: DM\n"
            "---\n"
            "Geheim\n"
        )

        migrated, disposition = migrate_document_text(
            content,
            Path("Waffenkammer/Methammer.md"),
            {},
        )
        metadata, _ = split_frontmatter(migrated)

        self.assertEqual(metadata["sichtbarkeit"], [])
        self.assertEqual(metadata["zugriff"], "spielleitung")
        self.assertEqual(metadata["status"], "vorbereitet")
        self.assertEqual(disposition, "game-master")

    def test_migration_is_idempotent(self) -> None:
        content = "---\ntyp: Beschreibung\n---\nPublic\n"
        first, _ = migrate_document_text(content, Path("Public.md"), {})
        second, _ = migrate_document_text(first, Path("Public.md"), {})

        self.assertEqual(first, second)
        self.assertIsInstance(split_frontmatter(first)[0]["sichtbarkeit"], list)


if __name__ == "__main__":
    unittest.main()