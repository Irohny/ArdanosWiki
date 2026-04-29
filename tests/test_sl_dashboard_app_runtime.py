import unittest

from sl_dashboard.app_runtime import _resolve_session_select_state


class SessionSelectorStateTests(unittest.TestCase):
    def test_pending_selection_takes_precedence(self) -> None:
        self.assertEqual(
            _resolve_session_select_state(
                ["mord-und-verlobung", "neue-runde"],
                "mord-und-verlobung",
                "neue-runde",
            ),
            ("neue-runde", True),
        )

    def test_invalid_current_selection_falls_back_to_first_option(self) -> None:
        self.assertEqual(
            _resolve_session_select_state(
                ["mord-und-verlobung", "neue-runde"],
                "unbekannt",
                None,
            ),
            ("mord-und-verlobung", False),
        )

    def test_invalid_pending_selection_is_consumed(self) -> None:
        self.assertEqual(
            _resolve_session_select_state(
                ["mord-und-verlobung", "neue-runde"],
                "mord-und-verlobung",
                "nicht-da",
            ),
            ("mord-und-verlobung", True),
        )


if __name__ == "__main__":
    unittest.main()