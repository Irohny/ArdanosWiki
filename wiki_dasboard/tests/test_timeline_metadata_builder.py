import tempfile
import unittest
from pathlib import Path

from wiki_dasboard.config import cfg
from wiki_dasboard.extraktion_tools.metadata_extractor.build_timeline_json import (
    build_items_for_profile,
    load_profiles,
    parse_timeline_page,
)


class TimelineMetadataBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.world_root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_page(self, relative_path: str, frontmatter: str) -> Path:
        path = self.world_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n", encoding="utf-8")
        return path

    def test_builds_ruler_range_from_tags_and_year_fields(self) -> None:
        page = self.write_page(
            "Kaiserreich/Vaylen/NPCs/Fuersten/Selene.md",
            'tags: ["Fürst"]\nzeit_von_jahr: "2153"\nzeit_bis_jahr:',
        )

        item = parse_timeline_page(page, self.world_root)

        self.assertEqual(item["primary_types"], ["Herrscher"])
        self.assertEqual(item["categories"], ["Vaylen"])
        self.assertEqual(item["parsed_timespan"]["start"], 2153)
        self.assertEqual(item["parsed_timespan"]["end"], 2486)
        self.assertEqual(item["parsed_timespan"]["kind"], "range")

    def test_builds_foundation_from_tag(self) -> None:
        page = self.write_page(
            "Kaiserreich/Drakmora/Drakmora.md",
            "tags: [Gründung]\nzeit_von_jahr: 610\nzeit_bis_jahr:",
        )

        item = parse_timeline_page(page, self.world_root)

        self.assertEqual(item["primary_types"], ["Gruendung"])
        self.assertEqual(item["parsed_timespan"], {
            "kind": "point",
            "start": 610,
            "end": 610,
        })

    def test_event_tag_categories_feed_matching_principality_profile(self) -> None:
        page = self.write_page(
            "Kaiserreich/Geschichte/Brueckenkrieg.md",
            "tags: [Ereignis, Elmrath, Mariven]\n"
            'zeit_von_jahr: "2464"\nzeit_bis_jahr: "2466"',
        )

        item = parse_timeline_page(page, self.world_root)
        profile = load_profiles()["mariven"]
        built_items = build_items_for_profile([item], profile)
        elmrath_items = build_items_for_profile([item], load_profiles()["elmrath"])

        self.assertEqual(item["categories"], ["Elmrath", "Mariven"])
        self.assertEqual(len(built_items), 1)
        self.assertEqual(built_items[0]["column"], "mariven_ranges")
        self.assertEqual(len(elmrath_items), 1)
        self.assertEqual(elmrath_items[0]["column"], "elmrath_ranges")
        self.assertEqual((built_items[0]["start"], built_items[0]["end"]), (2464, 2466))

    def test_reads_timeline_pages_outside_kaiserreich_from_explicit_tags(self) -> None:
        page = self.write_page(
            "Geschichten/Erzaehlungen/Marivener Ereignis.md",
            "tags: [Geschichte, Mariven]\nzeit_von_jahr: 2440",
        )

        item = parse_timeline_page(page, self.world_root)

        self.assertEqual(item["categories"], ["Mariven"])
        self.assertEqual(item["parsed_timespan"]["kind"], "point")

    def test_reads_single_region_field_outside_region_folders(self) -> None:
        page = self.write_page(
            "Geschichten/Ereignisse/Drakmora-Krieg.md",
            'region: "[[Drakmora]]"\n'
            "tags: [Krieg]\nzeit_von_jahr: 2440",
        )

        item = parse_timeline_page(page, self.world_root)

        self.assertEqual(item["categories"], ["Drakmora"])

    def test_reads_multiple_regions_from_region_field(self) -> None:
        page = self.write_page(
            "Geschichten/Ereignisse/Handelskrieg.md",
            'Region:\n  - "[[Elmrath]]"\n  - "[[Mariven]]"\n'
            "tags: [Ereignisse]\nzeit_von_jahr: 2464\nzeit_bis_jahr: 2466",
        )
        item = parse_timeline_page(page, self.world_root)
        profile = load_profiles()["mariven"]
        built_items = build_items_for_profile([item], profile)

        self.assertEqual(item["categories"], ["Elmrath", "Mariven"])
        self.assertEqual(len(built_items), 1)
        self.assertEqual(built_items[0]["column"], "mariven_ranges")

    def test_reads_planned_timeline_tags(self) -> None:
        planned_tags = {
            "Ergeignis": "Ereignis",
            "Ereignisse": "Ereignis",
            "Gründung": "Gruendung",
            "Krieg": "Ereignis",
            "Fürst": "Herrscher",
            "König": "Herrscher",
            "Kaiser": "Herrscher",
        }

        for index, (tag, expected_type) in enumerate(planned_tags.items()):
            with self.subTest(tag=tag):
                page = self.write_page(
                    f"Kaiserreich/Elmrath/Test-{index}.md",
                    f"tags: [{tag}]\nzeit_von_jahr: 2400",
                )

                item = parse_timeline_page(page, self.world_root)

                self.assertIsNotNone(item)
                self.assertEqual(item["primary_types"], [expected_type])

    def test_all_profiles_write_svgs_to_timelines_directory(self) -> None:
        profiles = load_profiles()

        self.assertTrue(
            all(
                profile["output_file"].parent
                == cfg.REPO_ROOT
                / "World"
                / "Images"
                / "Timelines"
                for profile in profiles.values()
            )
        )

    def test_time_column_matches_era_bar_and_redistributes_width_evenly(self) -> None:
        profiles = load_profiles()
        realm_columns = profiles["realm"]["columns"]
        realm_time = next(column for column in realm_columns if column["id"] == "world")
        realm_others = [column for column in realm_columns if column["id"] != "world"]

        self.assertEqual((realm_time["width"], realm_time["lanes"]), (57, 1))
        self.assertTrue(all(column["width"] == 165.5 for column in realm_others))
        self.assertEqual(sum(column["width"] for column in realm_columns), 1050)

        for profile_id in ("elmrath", "drakmora", "mariven", "schwarzklamm", "vaylen"):
            columns = profiles[profile_id]["columns"]
            time_column = next(column for column in columns if column["id"] == "world")
            other_widths = [column["width"] for column in columns if column["id"] != "world"]

            with self.subTest(profile=profile_id):
                self.assertEqual((time_column["width"], time_column["lanes"]), (57, 1))
                self.assertEqual(other_widths, [191, 176, 176])
                self.assertEqual(sum(column["width"] for column in columns), 600)

    def test_world_events_fit_the_single_time_lane(self) -> None:
        page = self.write_page(
            "Kaiserreich/Geschichte/Weltweites Ereignis.md",
            "tags: [Ereignis, Weltgeschichte]\nzeit_von_jahr: 2400",
        )

        item = parse_timeline_page(page, self.world_root)
        built_items = build_items_for_profile([item], load_profiles()["realm"])

        self.assertEqual(len(built_items), 1)
        self.assertEqual(built_items[0]["column"], "world")
        self.assertEqual(built_items[0]["lane"], 0)

    def test_ignores_art_even_when_it_has_a_war_tag(self) -> None:
        page = self.write_page(
            "Kaiserreich/Drakmora/Kuenstler/Bild.md",
            "tags: [maler, kunst, drakmora, krieg]\nzeit_von_jahr: 2429",
        )

        self.assertIsNone(parse_timeline_page(page, self.world_root))


if __name__ == "__main__":
    unittest.main()