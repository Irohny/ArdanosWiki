from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from wiki_dasboard.components.access_control import (
    campaigns_for_user,
    can_view_document,
    filter_document_sections,
)
from wiki_dasboard.components.utils import find_markdown_files, get_all_file_paths
from wiki_dasboard.components.login import Roles, User
from wiki_dasboard.configs import KampagneConfig
from wiki_dasboard.config import cfg


def _user(name: str, role: str = "Player", character_ids=()) -> User:
    return User(
        name=name,
        role=Roles(role),
        loged_in=True,
        character_ids=character_ids,
    )


class DocumentAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.world_root = Path(self.temporary_directory.name) / "World"
        self.world_root.mkdir()

    def _write_document(self, relative_path: str, content: str) -> Path:
        path = self.world_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_explicit_character_grant_only_allows_assigned_character(self) -> None:
        document = self._write_document(
            "Tashioren.md",
            "---\nsichtbarkeit: [vishuda]\n---\nDetails",
        )

        self.assertTrue(
            can_view_document(document, _user("Vishuda", character_ids=("vishuda",)), self.world_root)
        )
        self.assertFalse(
            can_view_document(document, _user("Gnodomir", character_ids=("gnodomir",)), self.world_root)
        )

    def test_character_grant_and_campaign_filter_are_separate(self) -> None:
        document = self._write_document(
            "Gischtgeborenen.md",
            "---\n"
            "kampagne:\n  - '[[Schatten der Zeit]]'\n"
            "sichtbarkeit: [gnodomir]\n"
            "---\nGemeinsame Informationen",
        )

        self.assertTrue(
            can_view_document(
                document,
                _user("Gnodomir", character_ids=("gnodomir",)),
                self.world_root,
                character_campaigns={"gnodomir": ("kampange 1",)},
                campaign_aliases={
                    "Kampange 1": "campaign_01",
                    "Schatten der Zeit": "campaign_01",
                },
            )
        )

    def test_campaign_alias_uses_configured_player_facing_name(self) -> None:
        campaign = KampagneConfig(
            campaign_id="campaign_custom",
            campaign_name="Der gemappte Name",
            alias="Interner Arbeitsname",
        )
        user = User(
            name="Vishuda",
            user_name="vishuda-login",
            role=Roles.Player,
            loged_in=True,
            character_ids=("vishuda",),
            campaigns=(campaign,),
        )

        with patch(
            "wiki_dasboard.components.access_control.build_character_campaign_index",
            return_value={},
        ):
            campaigns = campaigns_for_user(user, self.world_root)

        self.assertEqual(campaigns, (("campaign_custom", "Der gemappte Name"),))

    def test_missing_acl_fails_closed_for_players(self) -> None:
        document = self._write_document("gn_Gnodomir/gn_Backstory.md", "Text")

        self.assertFalse(can_view_document(document, _user("Vishuda"), self.world_root))
        self.assertFalse(can_view_document(document, _user("Gnodomir"), self.world_root))

    def test_invalid_acl_fails_closed_for_players(self) -> None:
        document = self._write_document(
            "Bad.md", "---\nsichtbarkeit: invalid\n---\nText"
        )

        self.assertFalse(can_view_document(document, _user("Gnodomir"), self.world_root))

    def test_missing_section_target_fails_closed(self) -> None:
        content = (
            "---\n"
            "sichtbarkeit: []\n"
            "abschnitt_sichtbarkeit:\n"
            "  'Nicht vorhandene Details': [vishuda]\n"
            "---\n"
            "## Bekannte Details\nText"
        )

        self.assertEqual(filter_document_sections(content, _user("Vishuda")), "")

    def test_paths_outside_world_are_denied_even_to_game_masters(self) -> None:
        outside_document = Path(self.temporary_directory.name) / "outside.md"
        outside_document.write_text("Text", encoding="utf-8")

        self.assertFalse(
            can_view_document(
                outside_document,
                _user("Admin", "GameMaster"),
                self.world_root,
            )
        )

    def test_section_grant_hides_heading_and_nested_content_from_other_characters(self) -> None:
        content = (
            "---\n"
            "sichtbarkeit: []\n"
            "abschnitt_sichtbarkeit:\n"
            "  'Geheime Details': [vishuda]\n"
            "---\n"
            "# Tashioren\n"
            "Allgemeine Information.\n"
            "## Geheime **Details**\n"
            "Nur Vishuda.\n"
            "### Unterabschnitt\n"
            "Auch verborgen.\n"
            "## Offener Schluss\n"
            "Wieder sichtbar."
        )

        gnodomir = filter_document_sections(
            content, _user("Gnodomir", character_ids=("gnodomir",))
        )
        vishuda = filter_document_sections(
            content, _user("Vishuda", character_ids=("vishuda",))
        )

        self.assertIn("Allgemeine Information.", gnodomir)
        self.assertNotIn("Geheime", gnodomir)
        self.assertNotIn("Auch verborgen.", gnodomir)
        self.assertIn("Wieder sichtbar.", gnodomir)
        self.assertIn("Nur Vishuda.", vishuda)

    def test_heading_inside_code_fence_does_not_match_section_acl(self) -> None:
        content = (
            "---\n"
            "sichtbarkeit: []\n"
            "abschnitt_sichtbarkeit:\n"
            "  'Geheime Details': []\n"
            "---\n"
            "```markdown\n"
            "## Geheime Details\n"
            "```\n"
        )

        filtered = filter_document_sections(
            content, _user("Gnodomir", character_ids=("gnodomir",))
        )

        self.assertEqual(filtered, "")

    def test_empty_section_grant_is_game_master_only(self) -> None:
        content = (
            "---\n"
            "sichtbarkeit: []\n"
            "abschnitt_sichtbarkeit:\n"
            "  'Geheime Details': []\n"
            "---\n"
            "## Geheime Details\nNur Spielleitung.\n"
        )

        filtered = filter_document_sections(
            content, _user("Gnodomir", character_ids=("gnodomir",))
        )

        self.assertNotIn("Nur Spielleitung.", filtered)

    def test_private_headings_and_their_sections_are_hidden_from_players(self) -> None:
        content = (
            "---\nsichtbarkeit: []\n---\n"
            "## Ziele\nZieltext\n"
            "## Plot-Hooks\nHooktext\n"
            "## Geheime Informationen\nGeheimtext\n"
            "## Spielleiter\nLeitungstext\n"
            "## Kampfwerte\nKampftext\n"
            "## Öffentlicher Schluss\nOffen\n"
        )

        filtered = filter_document_sections(content, _user("Gnodomir"))
        game_master_content = filter_document_sections(
            content, _user("Admin", "GameMaster")
        )

        for private_text in (
            "Ziele",
            "Zieltext",
            "Plot-Hooks",
            "Hooktext",
            "Geheime Informationen",
            "Geheimtext",
            "Spielleiter",
            "Leitungstext",
            "Kampfwerte",
            "Kampftext",
        ):
            self.assertNotIn(private_text, filtered)
        self.assertIn("Offen", filtered)
        self.assertEqual(game_master_content, content)

    def test_secret_information_is_shared_by_document_character_grants(self) -> None:
        content = (
            "---\nsichtbarkeit: [vishuda]\n---\n"
            "## Geheime Informationen\nNur für Vishuda.\n"
            "## Öffentlicher Schluss\nOffen\n"
        )

        vishuda = filter_document_sections(
            content, _user("Vishuda", character_ids=("vishuda",))
        )
        gnodomir = filter_document_sections(
            content, _user("Gnodomir", character_ids=("gnodomir",))
        )

        self.assertNotIn("Geheime Informationen", vishuda)
        self.assertIn("Nur für Vishuda.", vishuda)
        self.assertNotIn("Nur für Vishuda.", gnodomir)
        self.assertIn("Offen", gnodomir)

    def test_secret_information_uses_explicit_section_grants_when_present(self) -> None:
        content = (
            "---\n"
            "sichtbarkeit: []\n"
            "abschnitt_sichtbarkeit:\n"
            "  'Geheime Informationen': [vishuda]\n"
            "---\n"
            "## Geheime Informationen\nNur für Vishuda.\n"
        )

        vishuda = filter_document_sections(
            content, _user("Vishuda", character_ids=("vishuda",))
        )
        gnodomir = filter_document_sections(
            content, _user("Gnodomir", character_ids=("gnodomir",))
        )

        self.assertNotIn("Geheime Informationen", vishuda)
        self.assertIn("Nur für Vishuda.", vishuda)
        self.assertNotIn("Nur für Vishuda.", gnodomir)

    def test_empty_secret_information_grant_overrides_document_grant(self) -> None:
        content = (
            "---\n"
            "sichtbarkeit: [vishuda]\n"
            "abschnitt_sichtbarkeit:\n"
            "  'Geheime Informationen': []\n"
            "---\n"
            "## Geheime Informationen\nNur Spielleitung.\n"
        )

        filtered = filter_document_sections(
            content, _user("Vishuda", character_ids=("vishuda",))
        )

        self.assertNotIn("Nur Spielleitung.", filtered)


    def test_tashioren_member_list_is_visible_only_to_vishuda(self) -> None:
        document = (
            Path(__file__).resolve().parents[2]
            / "World/Gruppen/Tashioren/Tashiro'en.md"
        )
        content = document.read_text(encoding="utf-8")

        gnodomir_content = filter_document_sections(
            content, _user("Gnodomir", character_ids=("gnodomir",))
        )
        vishuda_content = filter_document_sections(
            content, _user("Vishuda", character_ids=("vishuda",))
        )

        self.assertIn("Der **Orden der lautlosen Blüte**", gnodomir_content)
        self.assertNotIn("- [[Suruya]]", gnodomir_content)
        self.assertIn("- [[Suruya]]", vishuda_content)

    def test_campaign_tree_uses_character_grants_and_prunes_empty_folders(self) -> None:
        (self.world_root / "Gnodomir.md").write_text(
            "---\ncharakter_id: gnodomir\n"
            "kampagne: ['[[Schatten der Zeit]]']\n---\n",
            encoding="utf-8",
        )
        (self.world_root / "Vishuda.md").write_text(
            "---\ncharakter_id: vishuda\n"
            "kampagne: ['[[Schatten der Zeit]]']\n---\n",
            encoding="utf-8",
        )
        self._write_document(
            "Gischtgeborene/Gischtgeborenen.md",
            "---\nkampagne: ['[[Schatten der Zeit]]']\n"
            "sichtbarkeit: [gnodomir, vishuda]\n---\n",
        )
        self._write_document(
            "Tashioren/Tashiro'en.md",
            "---\nkampagne: ['[[Schatten der Zeit]]']\n"
            "sichtbarkeit: [gnodomir, vishuda]\n"
            "abschnitt_sichtbarkeit:\n    'Weitere Details': [vishuda]\n"
            "---\n## Weitere Details\nNur Vishuda.\n",
        )
        self._write_document("Tashioren/Notiz.md", "---\nstatus: DM\n---\n")

        tree = find_markdown_files(
            str(self.world_root),
            _user("Gnodomir", character_ids=("gnodomir",)),
            campaign_id=cfg.player_access.campaign_aliases["Schatten der Zeit"],
        )
        visible_paths = get_all_file_paths(tree)

        self.assertIn(str(self.world_root / "Gischtgeborene/Gischtgeborenen.md"), visible_paths)
        self.assertIn(str(self.world_root / "Tashioren/Tashiro'en.md"), visible_paths)
        self.assertNotIn(str(self.world_root / "Tashioren/Notiz.md"), visible_paths)
        self.assertIn(str(self.world_root / "Tashioren"), tree[str(self.world_root)])


if __name__ == "__main__":
    unittest.main()