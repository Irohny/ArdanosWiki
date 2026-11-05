from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from wiki_dasboard.configs.markdown_loader import load_player_access_registry


class MarkdownAccessConfigTests(unittest.TestCase):
    def test_builds_player_and_campaign_config_from_markdown_sources(self) -> None:
        with TemporaryDirectory() as directory:
            world_root = Path(directory) / "World"
            access_dir = world_root / "Zugriffsrechte"
            character_dir = world_root / "Characters"
            access_dir.mkdir(parents=True)
            character_dir.mkdir()
            (access_dir / "Spielerrechte.md").write_text(
                "---\ntyp: Hilfsmittel\nstatus: DM\n---\n"
                "# [[Frido]]\n"
                "**username:** [[frido-login|Frido Login]]\n"
                "**role**: player\n"
                "**charaktere**:\n"
                "- [[Hero One|Hero]]\n"
                "**kampangen:**\n"
                "- [[Work Title|The Work]]\n"
                "\n# Incomplete\n"
                "**username:** [[incomplete-login]]\n",
                encoding="utf-8",
            )
            (access_dir / "Kampangen Mappings.md").write_text(
                "---\ntyp: Hilfsmittel\nstatus: DM\n---\n"
                "| Kampangen Name | Alias |\n"
                "| --- | --- |\n"
                "| [[The Display Name|Display]] | [[Work Title|Old Work Title]] |\n",
                encoding="utf-8",
            )
            (character_dir / "Hero One.md").write_text(
                "---\ntyp: Spieler\ncharakter_id: hero-one\n---\n",
                encoding="utf-8",
            )

            registry = load_player_access_registry(world_root)

        self.assertEqual(len(registry.players), 1)
        player = registry.players[0]
        self.assertEqual(player.name, "Frido")
        self.assertEqual(player.user_name, "frido-login")
        self.assertEqual(player.role, "Player")
        self.assertEqual(player.charakter, ("hero-one",))
        self.assertEqual(
            player.campaigns[0].campaign_id,
            "the-display-name",
        )
        self.assertEqual(
            registry.campaign_labels,
            {"the-display-name": "The Display Name"},
        )
        self.assertEqual(
            registry.campaign_aliases,
            {
                "The Display Name": "the-display-name",
                "Work Title": "the-display-name",
            },
        )


if __name__ == "__main__":
    unittest.main()