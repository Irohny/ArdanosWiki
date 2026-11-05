from enum import Enum
import subprocess
import sys
import unittest

from wiki_dasboard.components.encounter_calculator import (
    EncounterOptionen,
    MonsterEintrag,
    MonsterTag,
    Party,
    Terrainlage,
    Ueberraschung,
    action_weight_for_entry,
    encounter_multiplikator,
    solo_boss_factor,
    target_index,
    target_xp,
    threat_modifier_bounds,
    threat_modifier_for_entry,
    xp_grenzen,
)


class EncounterCalculatorTests(unittest.TestCase):
    def test_target_helpers_accept_stale_difficulty_enum_values(self) -> None:
        class StaleSchwierigkeit(Enum):
            MITTEL = "Mittel"

        party = Party(spieler=4, stufe=5)
        thresholds = xp_grenzen(party)

        self.assertEqual(target_index(StaleSchwierigkeit.MITTEL), 2)
        self.assertEqual(target_xp(party, StaleSchwierigkeit.MITTEL, thresholds), 2500)

    def test_import_succeeds_without_login_utils_cycle(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import wiki_dasboard.components.encounter_calculator",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_monster_multiplier_adjustment_by_party_size(self) -> None:
        expected = {
            2: 2.5,
            3: 2.0,
            4: 2.0,
            6: 1.5,
        }

        for party_size, multiplier in expected.items():
            with self.subTest(party_size=party_size):
                self.assertEqual(encounter_multiplikator(3, party_size), multiplier)

    def test_solo_monster_is_not_given_second_base_penalty(self) -> None:
        options = EncounterOptionen(
            terrain=Terrainlage.NEUTRAL,
            ueberraschung=Ueberraschung.KEINE,
            legendare_aktionen=False,
            legendare_resistenzen=False,
            phasenwechsel=False,
            gegner_beschwoeren=False,
            wellen=1,
            kurze_pause_zwischen_wellen=False,
            heilfenster_zwischen_wellen=False,
            gleiches_kampffeld=True,
        )

        factor = solo_boss_factor(
            Party(spieler=4, stufe=5), [MonsterEintrag(cr=5, anzahl=1)], options
        )

        self.assertEqual(factor, 1.0)

    def test_2014_party_thresholds_remain_unchanged(self) -> None:
        self.assertEqual(
            xp_grenzen(Party(spieler=4, stufe=1)),
            {"LEICHT": 100, "MITTEL": 200, "SCHWER": 300, "TÖDLICH": 400},
        )

    def test_tags_in_same_dimension_do_not_stack(self) -> None:
        monster = MonsterEintrag(
            cr=1,
            anzahl=1,
            tags=(MonsterTag.BURST, MonsterTag.FLAECHE),
        )

        self.assertEqual(threat_modifier_for_entry(monster), 1.18)

    def test_distinct_factor_dimensions_stack_once(self) -> None:
        monster = MonsterEintrag(
            cr=1,
            anzahl=1,
            tags=(MonsterTag.BURST, MonsterTag.CONTROL, MonsterTag.TANK),
        )

        self.assertEqual(threat_modifier_for_entry(monster), 1.43)

    def test_profile_confidence_sets_threat_modifier_interval(self) -> None:
        monster = MonsterEintrag(
            cr=1,
            anzahl=1,
            tags=(MonsterTag.CONTROL,),
            profilsicherheit=0.5,
        )

        lower, upper = threat_modifier_bounds(monster)
        self.assertAlmostEqual(lower, 1.1)
        self.assertAlmostEqual(upper, 1.3)

    def test_tags_do_not_add_actions_a_second_time(self) -> None:
        monster = MonsterEintrag(
            cr=1,
            anzahl=1,
            tags=(MonsterTag.MOBIL, MonsterTag.FERNKAMPF),
        )

        self.assertEqual(action_weight_for_entry(monster), 1.0)


if __name__ == "__main__":
    unittest.main()