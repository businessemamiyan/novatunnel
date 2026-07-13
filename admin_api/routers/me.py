from fastapi import APIRouter, Depends

from shared import db
from auth import get_current_user

router = APIRouter()


@router.get("")
async def get_me(user: dict = Depends(get_current_user)):
    is_admin = await db.is_admin(user["telegram_id"])
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    return {
        "telegram_id": user["telegram_id"],
        "first_name": user["first_name"],
        "username": user["username"],
        "is_admin": is_admin,
        "gift_balance_gb": float(db_user["gift_balance_gb"]) if db_user else 0,
        "wallet_balance_toman": int(db_user["wallet_balance_toman"]) if db_user else 0,
        "reward_credit_toman": int(db_user["reward_credit_toman"]) if db_user else 0,
        "phone_verified": db_user["phone_verified"] if db_user else False,
        "onboarding_seen": db_user["onboarding_seen"] if db_user else False,
    }


@router.post("/onboarding-seen")
async def set_onboarding_seen(user: dict = Depends(get_current_user)):
    await db.mark_onboarding_seen(user["telegram_id"])
    return {"ok": True}
