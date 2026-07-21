import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import auth as panel_auth
from shared import db

router = APIRouter()


class TelegramLoginPayload(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_token_pair(telegram_id: int) -> dict:
    return {
        "access_token": panel_auth.create_access_token(telegram_id),
        "refresh_token": panel_auth.create_refresh_token(telegram_id),
        "token_type": "bearer",
    }


async def _store_refresh_token(telegram_id: int, refresh_token: str):
    payload = panel_auth.decode_refresh_token(refresh_token)
    expires_at = datetime.datetime.fromtimestamp(payload["exp"], tz=datetime.timezone.utc)
    await db.create_admin_refresh_token(telegram_id, panel_auth.hash_refresh_token(refresh_token), expires_at)


@router.post("/telegram-login")
async def telegram_login(payload: TelegramLoginPayload):
    try:
        verified = panel_auth.verify_telegram_login_widget(payload.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(401, str(e))

    telegram_id = int(verified["id"])
    if not await db.is_admin(telegram_id):
        raise HTTPException(403, "این حساب تلگرام ادمین نیست")

    tokens = _issue_token_pair(telegram_id)
    await _store_refresh_token(telegram_id, tokens["refresh_token"])
    return tokens


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    payload = panel_auth.decode_refresh_token(body.refresh_token)
    telegram_id = int(payload["sub"])

    token_hash = panel_auth.hash_refresh_token(body.refresh_token)
    stored = await db.get_admin_refresh_token(token_hash)
    if stored is None or stored["revoked_at"] is not None:
        raise HTTPException(401, "refresh token revoked or unknown")
    if stored["expires_at"] < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(401, "refresh token expired")

    if not await db.is_admin(telegram_id):
        raise HTTPException(403, "این حساب تلگرام دیگر ادمین نیست")

    await db.revoke_admin_refresh_token(token_hash)
    tokens = _issue_token_pair(telegram_id)
    await _store_refresh_token(telegram_id, tokens["refresh_token"])
    return tokens


@router.post("/logout")
async def logout(body: RefreshRequest):
    await db.revoke_admin_refresh_token(panel_auth.hash_refresh_token(body.refresh_token))
    return {"ok": True}


@router.get("/me")
async def me(admin: dict = Depends(panel_auth.get_current_admin)):
    return admin
