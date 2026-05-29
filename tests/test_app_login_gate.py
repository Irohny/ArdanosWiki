from pathlib import Path
import unittest
from unittest.mock import patch

import app
from streamlit.testing.v1 import AppTest


APP_FILE = Path(__file__).resolve().parents[1] / "app.py"
LINKS_PAGE = "World/Links.md"


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

    def test_page_query_param_survives_login(self) -> None:
        at = _build_app_test()

        at.query_params["page"] = LINKS_PAGE
        at.run(timeout=30)

        self.assertEqual(at.query_params["page"], [LINKS_PAGE])
        at.text_input(key="charackter_name").set_value("Admin")
        at.text_input(key="password").set_value("Schattenherz")
        at.button[0].click()
        at.run(timeout=30)

        self.assertEqual(at.session_state["current_path"], LINKS_PAGE)
        self.assertIn(":red[Links]", [element.value for element in at.title])

    def test_cookie_claims_restore_logged_in_user(self) -> None:
        with patch("app.load_auth_claims_from_cookie", return_value={"name": "Admin", "role": "GameMaster"}):
            restored_user = app.restore_persisted_user()

        self.assertIsNotNone(restored_user)
        self.assertEqual(restored_user.name, "Admin")
        self.assertTrue(restored_user.loged_in)


if __name__ == "__main__":
    unittest.main()