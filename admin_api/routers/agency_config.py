from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class AgencyTierUpdate(BaseModel):
    activation_fee_toman: int
    purchase_rate_toman_per_gb: int
    min_wallet_balance_toman: int


@router.get("")
async def list_agency_tiers(admin: dict = Depends(get_current_admin)):
    rows = await db.get_agency_tier_config()
    return [dict(r) for r in rows]


@router.patch("/{tier}")
async def update_agency_tier(tier: str, body: AgencyTierUpdate, admin: dict = Depends(get_current_admin)):
    updated = await db.update_agency_tier_config(
        tier, body.activation_fee_toman, body.purchase_rate_toman_per_gb, body.min_wallet_balance_toman
    )
    if updated is None:
        raise HTTPException(404, "not found")
    await db.log_admin_action(
        admin["telegram_id"], "agency_tier_config_update", f"tier {tier}",
        {
            "activation_fee_toman": body.activation_fee_toman,
            "purchase_rate_toman_per_gb": body.purchase_rate_toman_per_gb,
            "min_wallet_balance_toman": body.min_wallet_balance_toman,
        },
    )
    return dict(updated)
