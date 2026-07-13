from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class PriceUpdate(BaseModel):
    retail_price_toman: int


class BadgeUpdate(BaseModel):
    badge: str | None = None


@router.get("")
async def list_packages(admin: dict = Depends(get_current_admin)):
    rows = await db.get_packages_all()
    return [dict(r) for r in rows]


@router.patch("/{package_id}")
async def update_price(package_id: int, body: PriceUpdate, admin: dict = Depends(get_current_admin)):
    updated = await db.update_package_price(package_id, body.retail_price_toman)
    if updated is None:
        raise HTTPException(404, "not found")
    await db.log_admin_action(
        admin["telegram_id"], "package_price_update", f"package {package_id}",
        {"new_price": body.retail_price_toman},
    )
    return dict(updated)


@router.patch("/{package_id}/badge")
async def update_badge(package_id: int, body: BadgeUpdate, admin: dict = Depends(get_current_admin)):
    updated = await db.update_package_badge(package_id, body.badge)
    if updated is None:
        raise HTTPException(404, "not found")
    await db.log_admin_action(
        admin["telegram_id"], "package_badge_update", f"package {package_id}",
        {"new_badge": body.badge},
    )
    return dict(updated)
