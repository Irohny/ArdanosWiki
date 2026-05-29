from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
from typing import Any

import extra_streamlit_components as stx
import streamlit as st


AUTH_COOKIE_NAME = "ardanos_auth"
AUTH_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 14
AUTH_COOKIE_VERSION = 1


def get_cookie_manager() -> stx.CookieManager:
    return stx.CookieManager(key="ardanos-auth-cookie-manager")


def lookup_user_record(name: str) -> dict[str, Any] | None:
    normalized_name = name.strip()
    if not normalized_name:
        return None

    for user in st.secrets.get("users", []):
        if str(user.get("name", "")).strip() == normalized_name:
            return dict(user)
    return None


def _cookie_secret() -> bytes:
    configured_secret = str(st.secrets.get("cookie_secret", "")).strip()
    if configured_secret:
        return configured_secret.encode("utf-8")

    # Fallback for local compatibility if no dedicated secret exists yet.
    users_payload = json.dumps(list(st.secrets.get("users", [])), sort_keys=True)
    return hashlib.sha256(users_payload.encode("utf-8")).hexdigest().encode("utf-8")


def _encode_payload(payload: dict[str, Any]) -> str:
    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded_payload = urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(_cookie_secret(), payload_bytes, hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def _decode_payload(token: str) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None

    encoded_payload, signature = token.split(".", 1)
    padding = "=" * (-len(encoded_payload) % 4)

    try:
        payload_bytes = urlsafe_b64decode(f"{encoded_payload}{padding}")
    except (ValueError, TypeError):
        return None

    expected_signature = hmac.new(
        _cookie_secret(), payload_bytes, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, TypeError):
        return None

    if not isinstance(payload, dict):
        return None
    return payload


def _should_use_secure_cookie() -> bool:
    try:
        return bool(st.context.url.startswith("https://"))
    except Exception:
        return False


def persist_auth_claims(name: str, role: str) -> None:
    normalized_name = name.strip()
    normalized_role = role.strip()
    if not normalized_name or not normalized_role:
        return

    expires_at = datetime.now(UTC) + timedelta(seconds=AUTH_COOKIE_MAX_AGE_SECONDS)
    token = _encode_payload(
        {
            "v": AUTH_COOKIE_VERSION,
            "name": normalized_name,
            "role": normalized_role,
            "exp": int(expires_at.timestamp()),
        }
    )
    get_cookie_manager().set(
        AUTH_COOKIE_NAME,
        token,
        key="ardanos-auth-cookie-set",
        expires_at=expires_at,
        max_age=AUTH_COOKIE_MAX_AGE_SECONDS,
        secure=_should_use_secure_cookie(),
        same_site="lax",
    )


def clear_auth_cookie() -> None:
    get_cookie_manager().delete(AUTH_COOKIE_NAME, key="ardanos-auth-cookie-delete")


def load_auth_claims_from_cookie() -> dict[str, str] | None:
    token = get_cookie_manager().get(AUTH_COOKIE_NAME)
    if not token:
        return None

    payload = _decode_payload(str(token))
    if payload is None:
        clear_auth_cookie()
        return None

    if int(payload.get("v", 0)) != AUTH_COOKIE_VERSION:
        clear_auth_cookie()
        return None

    expires_at = int(payload.get("exp", 0))
    if expires_at <= int(datetime.now(UTC).timestamp()):
        clear_auth_cookie()
        return None

    name = str(payload.get("name", "")).strip()
    role = str(payload.get("role", "")).strip()
    if not name or not role:
        clear_auth_cookie()
        return None

    return {"name": name, "role": role}