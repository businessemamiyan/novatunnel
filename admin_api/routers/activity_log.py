from fastapi import APIRouter, Depends

from shared import db
from auth import get_current_admin

router = APIRouter()


@router.get("")
async def get_log(limit: int = 50, offset: int = 0, admin: dict = Depends(get_current_admin)):
    rows = await db.get_activity_log(limit, offset)
    return [dict(r) for r in rows]
