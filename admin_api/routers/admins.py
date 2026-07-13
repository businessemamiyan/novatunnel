from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class AdminAdd(BaseModel):
    telegram_id: int


@router.get("")
async def list_admins(admin: dict = Depends(get_current_admin)):
    rows = await db.list_admins()
    return [dict(r) for r in rows]


@router.post("")
async def add_admin(body: AdminAdd, admin: dict = Depends(get_current_admin)):
    await db.add_admin(body.telegram_id, admin["telegram_id"])
    await db.log_admin_action(admin["telegram_id"], "admin_add", str(body.telegram_id))
    return {"ok": True}


@router.delete("/{telegram_id}")
async def remove_admin(telegram_id: int, admin: dict = Depends(get_current_admin)):
    if await db.count_active_admins() <= 1:
        raise HTTPException(400, "cannot remove last admin")
    await db.remove_admin(telegram_id)
    await db.log_admin_action(admin["telegram_id"], "admin_remove", str(telegram_id))
    return {"ok": True}
