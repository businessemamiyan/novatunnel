import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException

import auth as panel_auth
from shared import config as shared_config


def _sign(payload: dict) -> str:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret_key = hashlib.sha256(shared_config.BOT_TOKEN.encode()).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def _valid_payload(**overrides):
    payload = {
        "id": 123456789,
        "first_name": "Admin",
        "username": "admin_user",
        "auth_date": int(time.time()),
    }
    payload.update(overrides)
    payload["hash"] = _sign(payload)
    return payload


def test_verify_telegram_login_widget_valid():
    payload = _valid_payload()
    result = panel_auth.verify_telegram_login_widget(payload)
    assert result["id"] == 123456789


def test_verify_telegram_login_widget_tampered_id_rejected():
    payload = _valid_payload()
    payload["id"] = 999999999  # هش برای id اصلی امضا شده بود، نه این
    with pytest.raises(ValueError, match="invalid hash"):
        panel_auth.verify_telegram_login_widget(payload)


def test_verify_telegram_login_widget_wrong_bot_token_rejected():
    payload = {
        "id": 123456789,
        "first_name": "Admin",
        "auth_date": int(time.time()),
    }
    wrong_secret = hashlib.sha256(b"some-other-bot-token").digest()
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    payload["hash"] = hmac.new(wrong_secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    with pytest.raises(ValueError, match="invalid hash"):
        panel_auth.verify_telegram_login_widget(payload)


def test_verify_telegram_login_widget_expired_rejected():
    old_auth_date = int(time.time()) - panel_auth.MAX_LOGIN_WIDGET_AGE_SECONDS - 3600
    payload = _valid_payload(auth_date=old_auth_date)
    with pytest.raises(ValueError, match="expired"):
        panel_auth.verify_telegram_login_widget(payload)


def test_verify_telegram_login_widget_missing_hash_rejected():
    with pytest.raises(ValueError, match="no hash"):
        panel_auth.verify_telegram_login_widget({"id": 1, "auth_date": int(time.time())})


def test_access_token_roundtrip():
    token = panel_auth.create_access_token(42)
    payload = panel_auth.decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_access_token_rejected_as_refresh():
    token = panel_auth.create_access_token(42)
    with pytest.raises(HTTPException):
        panel_auth.decode_refresh_token(token)


def test_refresh_token_roundtrip():
    token = panel_auth.create_refresh_token(42)
    payload = panel_auth.decode_refresh_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_decode_rejects_garbage_token():
    with pytest.raises(HTTPException):
        panel_auth.decode_access_token("not-a-real-jwt")


def test_hash_refresh_token_is_deterministic_sha256():
    token = "sample-refresh-token"
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert panel_auth.hash_refresh_token(token) == expected
    assert panel_auth.hash_refresh_token(token) == panel_auth.hash_refresh_token(token)
