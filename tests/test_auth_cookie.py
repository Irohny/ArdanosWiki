import unittest
from unittest.mock import patch

from components import auth


class _FakeCookieManager:
    def __init__(self) -> None:
        self.cookies: dict[str, str] = {}

    def get(self, cookie: str):
        return self.cookies.get(cookie)

    def set(self, cookie: str, val, **_kwargs):
        self.cookies[cookie] = str(val)

    def delete(self, cookie: str, **_kwargs):
        self.cookies.pop(cookie, None)


class AuthCookieTests(unittest.TestCase):
    def test_persisted_claims_roundtrip(self) -> None:
        cookie_manager = _FakeCookieManager()

        with patch("components.auth.get_cookie_manager", return_value=cookie_manager):
            with patch("components.auth._cookie_secret", return_value=b"test-secret"):
                auth.persist_auth_claims("Admin", "GameMaster")
                claims = auth.load_auth_claims_from_cookie()

        self.assertEqual(claims, {"name": "Admin", "role": "GameMaster"})

    def test_invalid_cookie_signature_is_rejected(self) -> None:
        cookie_manager = _FakeCookieManager()
        cookie_manager.cookies[auth.AUTH_COOKIE_NAME] = "invalid.token"

        with patch("components.auth.get_cookie_manager", return_value=cookie_manager):
            with patch("components.auth._cookie_secret", return_value=b"test-secret"):
                claims = auth.load_auth_claims_from_cookie()

        self.assertIsNone(claims)
        self.assertNotIn(auth.AUTH_COOKIE_NAME, cookie_manager.cookies)


if __name__ == "__main__":
    unittest.main()