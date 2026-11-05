import unittest
from unittest.mock import patch

from wiki_dasboard.components import auth


class _FakeCookieManager:
    def __init__(self) -> None:
        self.cookies: dict[str, str] = {}

    def get(self, cookie: str):
        return self.cookies.get(cookie)

    def set(self, cookie: str, val, **_kwargs):
        self.cookies[cookie] = str(val)

    def delete(self, cookie: str, **_kwargs):
        del self.cookies[cookie]


class AuthCookieTests(unittest.TestCase):
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
                claims = auth.load_auth_claims_from_cookie()

        self.assertEqual(claims, {"name": "Admin", "role": "GameMaster"})

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