import hashlib
import hmac
import time
import uuid

import jwt
from fastapi import Header, HTTPException

import config
from shared import config as shared_config, db

MAX_LOGIN_WIDGET_AGE_SECONDS = 86400


def verify_telegram_login_widget(payload: dict) -> dict:
    """تایید داده Telegram Login Widget — با initData ووب‌اپ فرق دارد:
    secret_key اینجا SHA256 خام bot_token است، نه HMAC با ثابت 'WebAppData' (بخش verify_init_data در admin_api/auth.py)."""
    data = dict(payload)
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise ValueError("no hash in payload")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()) if v is not None)

    secret_key = hashlib.sha256(shared_config.BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("invalid hash")

    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > MAX_LOGIN_WIDGET_AGE_SECONDS:
        raise ValueError("login widget payload expired")

    return data


def _create_token(telegram_id: int, token_type: str, ttl_seconds: int, extra: dict | None = None) -> str:
    now = int(time.time())
    payload = {
        "sub": str(telegram_id),
        "type": token_type,
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def create_access_token(telegram_id: int) -> str:
    return _create_token(telegram_id, "access", config.ACCESS_TOKEN_TTL_MINUTES * 60)


def create_refresh_token(telegram_id: int) -> str:
    return _create_token(telegram_id, "refresh", config.REFRESH_TOKEN_TTL_DAYS * 24 * 3600)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _decode(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid or expired token")
    if payload.get("type") != expected_type:
        raise HTTPException(401, "wrong token type")
    return payload


def decode_access_token(token: str) -> dict:
    return _decode(token, "access")


def decode_refresh_token(token: str) -> dict:
    return _decode(token, "refresh")


async def get_current_admin(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    telegram_id = int(payload["sub"])

    if not await db.is_admin(telegram_id):
        raise HTTPException(403, "not an admin")

    return {"telegram_id": telegram_id}
