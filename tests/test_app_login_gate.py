from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


APP_FILE = Path(__file__).resolve().parents[1] / "app.py"


def _build_app_test() -> AppTest:
    return AppTest.from_file(str(APP_FILE))


class AppLoginGateTests(unittest.TestCase):
    def test_app_requires_login_before_navigation(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)

        self.assertEqual([element.label for element in at.text_input], ["Charaktername:", "Passwort"])
        self.assertEqual([element.label for element in at.button], ["Login"])
        self.assertEqual([element.value for element in at.title], ["Login"])
        self.assertEqual(len(at.sidebar.button), 0)
        self.assertEqual(len(at.selectbox), 0)

    def test_valid_login_opens_main_app(self) -> None:
        at = _build_app_test()

        at.run(timeout=30)
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertTrue(at.session_state["user"].loged_in)
        self.assertIn(":red[Ardanos Wiki]", [element.value for element in at.title])
        self.assertIn("Logout", [element.label for element in at.sidebar.button])


if __name__ == "__main__":
    unittest.main()