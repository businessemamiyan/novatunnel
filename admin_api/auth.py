import hashlib
import hmac
import json
import logging
import time
from urllib.parse import unquote

from fastapi import Header, HTTPException

from shared import config, db

MAX_INIT_DATA_AGE_SECONDS = 86400
logger = logging.getLogger("auth")


def _parse_init_data(init_data: str) -> dict:
    """پارس دستی به‌جای parse_qsl — چون parse_qsl کاراکتر '+' را به space تبدیل می‌کند
    و initData تلگرام از این قرارداد form-encoding پیروی نمی‌کند؛ این باعث خراب شدن هش می‌شد."""
    result = {}
    for pair in init_data.split("&"):
        if not pair:
            continue
        key, _, value = pair.partition("=")
        result[unquote(key)] = unquote(value)
    return result


def verify_init_data(init_data: str) -> dict:
    logger.warning("verify_init_data: raw len=%d keys_seen=%s", len(init_data), init_data[:60])
    parsed = _parse_init_data(init_data)
    logger.warning("verify_init_data: parsed keys=%s", list(parsed.keys()))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("no hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        logger.warning(
            "verify_init_data: hash mismatch. computed=%s received=%s check_string=%r bot_token_prefix=%s",
            computed_hash, received_hash, data_check_string, config.BOT_TOKEN[:10],
        )
        raise ValueError("invalid hash")

    auth_date = int(parsed.get("auth_date", "0"))
    if time.time() - auth_date > MAX_INIT_DATA_AGE_SECONDS:
        raise ValueError("initData expired")

    user = json.loads(parsed["user"]) if "user" in parsed else None
    return {"user": user, "auth_date": auth_date}


async def get_current_admin(x_telegram_init_data: str = Header(...)) -> dict:
    try:
        verified = verify_init_data(x_telegram_init_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = verified.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="no user in initData")

    telegram_id = user["id"]
    if not await db.is_admin(telegram_id):
        raise HTTPException(status_code=403, detail="not an admin")

    return {
        "telegram_id": telegram_id,
        "first_name": user.get("first_name"),
        "username": user.get("username"),
    }


async def get_current_user(x_telegram_init_data: str = Header(...)) -> dict:
    """برای صفحات مشتری (نه ادمین) — فقط اعتبارسنجی initData، بدون نیاز به عضویت در bot_admins."""
    try:
        verified = verify_init_data(x_telegram_init_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = verified.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="no user in initData")

    return {
        "telegram_id": user["id"],
        "first_name": user.get("first_name"),
        "username": user.get("username"),
    }
