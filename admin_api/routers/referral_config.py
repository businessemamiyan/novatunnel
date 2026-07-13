from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class ReferralLevelUpdate(BaseModel):
    max_direct_children: int
    reward_percent: float
    monthly_cap_gb: float


@router.get("")
async def list_referral_levels(admin: dict = Depends(get_current_admin)):
    rows = await db.get_referral_level_config_list()
    return [dict(r) for r in rows]


@router.patch("/{level}")
async def update_referral_level(level: int, body: ReferralLevelUpdate, admin: dict = Depends(get_current_admin)):
    updated = await db.update_referral_level_config(
        level, body.max_direct_children, body.reward_percent, body.monthly_cap_gb
    )
    if updated is None:
        raise HTTPException(404, "not found")
    await db.log_admin_action(
        admin["telegram_id"], "referral_level_config_update", f"level {level}",
        {
            "max_direct_children": body.max_direct_children,
            "reward_percent": body.reward_percent,
            "monthly_cap_gb": body.monthly_cap_gb,
        },
    )
    return dict(updated)
