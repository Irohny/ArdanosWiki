import unittest

from sl_dashboard.components.encounter import _order_combatants_by_initiative
from sl_dashboard.models import EncounterCombatant


class EncounterOrderingTests(unittest.TestCase):
    def test_order_combatants_by_initiative_sorts_descending_and_moves_players_up(self) -> None:
        combatants = (
            EncounterCombatant(id="goblin", name="Goblin", side="enemy", initiative=12),
            EncounterCombatant(id="alyra", name="Alyra", side="player", source_type="player", initiative=16),
            EncounterCombatant(id="orc", name="Ork", side="enemy", initiative=18),
            EncounterCombatant(id="borin", name="Borin", side="player", source_type="player", initiative=None),
        )

        ordered_ids = tuple(
            combatant.id for combatant in _order_combatants_by_initiative(combatants)
        )

        self.assertEqual(ordered_ids, ("orc", "alyra", "goblin", "borin"))


if __name__ == "__main__":
    unittest.main()