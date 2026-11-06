import unittest
from types import SimpleNamespace
from unittest.mock import patch

from wiki_dasboard.components import auth, login
from wiki_dasboard.configs import (
    KampagneConfig,
    PlayerAccessConfig,
    PlayerAccessRegistryConfig,
)


class _FakeCookieManager:
    def __init__(self) -> None:
        self.cookies: dict[str, str] = {}
        self.get_all_calls = 0

    def get(self, cookie: str):
        return self.cookies.get(cookie)

    def get_all(self, **_kwargs):
        self.get_all_calls += 1
        return dict(self.cookies)

    def set(self, cookie: str, val, **_kwargs):
        self.cookies[cookie] = str(val)

    def delete(self, cookie: str, **_kwargs):
        del self.cookies[cookie]


class AuthCookieTests(unittest.TestCase):
    def test_cookie_manager_is_created_once_per_session(self) -> None:
        session_state = {}
        cookie_manager = _FakeCookieManager()

        with (
            patch("wiki_dasboard.components.auth.st.session_state", session_state),
            patch(
                "wiki_dasboard.components.auth.stx.CookieManager",
                return_value=cookie_manager,
            ) as create_manager,
        ):
            first = auth.get_cookie_manager()
            second = auth.get_cookie_manager()

        self.assertIs(first, cookie_manager)
        self.assertIs(second, cookie_manager)
        create_manager.assert_called_once_with(key="ardanos-auth-cookie-manager")

    def test_login_builds_user_from_username_access_record(self) -> None:
        state = {"user_name": "mira-login", "password": "secret-password"}
        record = {
            "name": "Mira",
            "user_name": "mira-login",
            "password": "secret-password",
            "role": "Player",
            "characters": ("vishuda", "nyssara"),
            "campaigns": (),
        }

        with (
            patch("wiki_dasboard.components.login.st.session_state", state),
            patch.object(login, "lookup_user_record", return_value=record),
            patch.object(login.utils, "find_markdown_files", return_value={"World": {}}),
            patch.object(login, "persist_auth_claims") as persist_claims,
        ):
            login.check_login_data()

        user = state["user"]
        self.assertEqual(user.name, "Mira")
        self.assertEqual(user.user_name, "mira-login")
        self.assertEqual(user.role, login.Roles.Player)
        self.assertEqual(user.character_ids, ("vishuda", "nyssara"))
        persist_claims.assert_called_once_with("mira-login", "Player")

    def test_user_name_secret_uses_configured_player_access(self) -> None:
        player = PlayerAccessConfig(
            name="Mira",
            user_name="mira-login",
            role="Player",
            charakter=("vishuda", "nyssara"),
            campaigns=(
                KampagneConfig("campaign_02", "Die Dämmerung", "Arbeitsname"),
            ),
        )
        registry = PlayerAccessRegistryConfig(players=(player,))
        secrets = {
            "users": [
                {
                    "user_name": "mira-login",
                    "password": "secret-password",
                    "role": "GameMaster",
                    "characters": ["untrusted-character"],
                }
            ]
        }

        with (
            patch("wiki_dasboard.components.auth.st.secrets", secrets),
            patch(
                "wiki_dasboard.components.auth.cfg",
                SimpleNamespace(player_access=registry),
            ),
        ):
            record = auth.lookup_user_record("MIRA-LOGIN")

        self.assertIsNotNone(record)
        self.assertEqual(record["password"], "secret-password")
        self.assertEqual(record["name"], "Mira")
        self.assertEqual(record["user_name"], "mira-login")
        self.assertEqual(record["role"], "Player")
        self.assertEqual(record["characters"], ("vishuda", "nyssara"))
        self.assertEqual(record["campaigns"], player.campaigns)

    def test_clear_missing_cookie_is_safe(self) -> None:
        cookie_manager = _FakeCookieManager()

        with patch("wiki_dasboard.components.auth.get_cookie_manager", return_value=cookie_manager):
            auth.clear_auth_cookie()

        self.assertEqual(cookie_manager.cookies, {})

    def test_persisted_claims_roundtrip(self) -> None:
        cookie_manager = _FakeCookieManager()

        with patch("wiki_dasboard.components.auth.get_cookie_manager", return_value=cookie_manager):
            with patch("wiki_dasboard.components.auth._cookie_secret", return_value=b"test-secret"):
                auth.persist_auth_claims("Admin", "GameMaster")
                with patch.object(cookie_manager, "get", return_value=None):
                    claims = auth.load_auth_claims_from_cookie()

        self.assertEqual(claims, {"name": "Admin", "role": "GameMaster"})
        self.assertEqual(cookie_manager.get_all_calls, 1)

    def test_invalid_cookie_signature_is_rejected(self) -> None:
        cookie_manager = _FakeCookieManager()
        cookie_manager.cookies[auth.AUTH_COOKIE_NAME] = "invalid.token"

        with patch("wiki_dasboard.components.auth.get_cookie_manager", return_value=cookie_manager):
            with patch("wiki_dasboard.components.auth._cookie_secret", return_value=b"test-secret"):
                claims = auth.load_auth_claims_from_cookie()

        self.assertIsNone(claims)
        self.assertNotIn(auth.AUTH_COOKIE_NAME, cookie_manager.cookies)


if __name__ == "__main__":
    unittest.main()