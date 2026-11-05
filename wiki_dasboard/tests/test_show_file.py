import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from wiki_dasboard.components.show_file import (
    WIKI_DIALOG_QUERY_PARAM,
    _extract_image_caption,
    make_internal_links_clickable,
    make_internal_links_main_page_clickable,
)


class ImageCaptionTests(unittest.TestCase):
    def test_extracts_inline_caption(self) -> None:
        self.assertEqual(
            _extract_image_caption(" _Inline caption_\nBody text"),
            ("Inline caption", "Body text"),
        )

    def test_extracts_caption_on_following_line(self) -> None:
        self.assertEqual(
            _extract_image_caption("\n_Next line caption_\nBody text"),
            ("Next line caption", "Body text"),
        )

    def test_keeps_regular_following_text(self) -> None:
        text = "\nRegular text"
        self.assertEqual(_extract_image_caption(text), (None, text))


class InternalWikiLinkTests(unittest.TestCase):
    target_path = "/wiki/World/Zauberarchiv/Schild.md"
    current_path = "/wiki/World/Zauberarchiv/Index.md"

    def test_archive_link_opens_target_as_main_page(self) -> None:
        with (
            patch(
                "wiki_dasboard.components.show_file.st.session_state",
                {"tree": {}, "current_path": self.current_path},
            ),
            patch(
                "wiki_dasboard.components.show_file.utils.find_file_path_in_tree",
                return_value=self.target_path,
            ),
        ):
            markup = make_internal_links_main_page_clickable("[[Schild]]")

        href = markup.split('href="', 1)[1].split('"', 1)[0]
        query = parse_qs(urlparse(href).query)
        self.assertEqual(query, {"page": [self.target_path]})
        self.assertNotIn(WIKI_DIALOG_QUERY_PARAM, query)

    def test_regular_wiki_link_still_opens_dialog(self) -> None:
        with (
            patch(
                "wiki_dasboard.components.show_file.st.session_state",
                {"tree": {}, "current_path": self.current_path},
            ),
            patch(
                "wiki_dasboard.components.show_file.utils.find_file_path_in_tree",
                return_value=self.target_path,
            ),
        ):
            markup = make_internal_links_clickable("[[Schild]]")

        href = markup.split('href="', 1)[1].split('"', 1)[0]
        query = parse_qs(urlparse(href).query)
        self.assertEqual(query["page"], [self.current_path])
        self.assertEqual(query[WIKI_DIALOG_QUERY_PARAM], [self.target_path])


if __name__ == "__main__":
    unittest.main()