from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from shared import db, marzban, qr, service_card
from auth import get_current_user

router = APIRouter()


@router.get("/packages")
async def my_packages(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        rows = await db.get_active_packages()
    else:
        rows = await db.get_purchasable_packages(db_user["id"], db_user["gift_balance_gb"])
    return [dict(r) for r in rows]


def _serialize_panel(p, status: str):
    return {
        "id": str(p["id"]),
        "label": p["label"] or p["marzban_username"],
        "status": status,
        "traffic_limit_gb": float(p["traffic_limit_gb"]) if p["traffic_limit_gb"] else 0,
        "traffic_used_gb": float(p["traffic_used_gb"]) if p["traffic_used_gb"] else 0,
        "expires_at": p["expires_at"].isoformat() if p["expires_at"] else None,
        "created_at": p["created_at"].isoformat(),
    }


@router.get("/services")
async def my_services(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        return []
    panels = await db.get_panels_for_user(db_user["id"])
    result = []
    for p in panels:
        marzban_user = await marzban.get_marzban_user(p["marzban_username"])
        status = service_card.compute_status(p, marzban_user)
        result.append(_serialize_panel(p, status))
    return result


@router.get("/services/{panel_id}")
async def service_detail(panel_id: str, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    panel = await db.get_panel(panel_id)
    if panel is None or db_user is None or panel["user_id"] != db_user["id"]:
        raise HTTPException(404, "not found")

    marzban_user = await marzban.get_marzban_user(panel["marzban_username"])
    sub_url = marzban.subscription_url(marzban_user) if marzban_user else None
    data = _serialize_panel(panel, service_card.compute_status(panel, marzban_user))
    data["subscription_url"] = sub_url
    data["links"] = marzban_user["links"] if marzban_user else []
    return data


@router.get("/services/{panel_id}/qr")
async def service_qr(panel_id: str, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    panel = await db.get_panel(panel_id)
    if panel is None or db_user is None or panel["user_id"] != db_user["id"]:
        raise HTTPException(404, "not found")

    marzban_user = await marzban.get_marzban_user(panel["marzban_username"])
    if marzban_user is None:
        raise HTTPException(404, "marzban user not found")

    sub_url = marzban.subscription_url(marzban_user)
    buf = qr.generate_branded_qr(sub_url)
    return StreamingResponse(buf, media_type="image/png")


async def _get_own_panel(panel_id: str, user: dict):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    panel = await db.get_panel(panel_id)
    if panel is None or db_user is None or panel["user_id"] != db_user["id"]:
        raise HTTPException(404, "not found")
    return panel


@router.post("/services/{panel_id}/toggle")
async def toggle_service(panel_id: str, user: dict = Depends(get_current_user)):
    panel = await _get_own_panel(panel_id, user)
    marzban_user = await marzban.get_marzban_user(panel["marzban_username"])
    if marzban_user is None:
        raise HTTPException(404, "marzban user not found")
    new_status = "disabled" if marzban_user.get("status") == "active" else "active"
    await marzban.set_service_status(panel["marzban_username"], new_status)
    return {"status": new_status}


@router.post("/services/{panel_id}/regenerate-link")
async def regenerate_link(panel_id: str, user: dict = Depends(get_current_user)):
    panel = await _get_own_panel(panel_id, user)
    marzban_user = await marzban.revoke_subscription(panel["marzban_username"])
    return {"subscription_url": marzban.subscription_url(marzban_user)}


def _serialize_person(r):
    return {
        "name": r["full_name"],
        "username": r["telegram_username"],
        "verified": r["phone_verified"],
    }


@router.get("/network")
async def my_network(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        return {"level1": [], "level2": [], "level3": [], "levels_meta": {}}

    level1 = await db.get_direct_referrals(db_user["id"])
    level2 = await db.get_referrals_for_users([r["id"] for r in level1])
    level3 = await db.get_referrals_for_users([r["id"] for r in level2])

    level_config = await db.get_referral_level_config()
    levels_meta = {}
    for level in (1, 2, 3):
        cfg = level_config[level]
        earned = await db.get_gb_awarded_this_month(db_user["id"], level)
        levels_meta[str(level)] = {
            "reward_percent": cfg["reward_percent"],
            "monthly_cap_gb": cfg["monthly_cap_gb"],
            "earned_this_month_gb": earned,
        }

    return {
        "level1": [_serialize_person(r) for r in level1],
        "level2": [_serialize_person(r) for r in level2],
        "level3": [_serialize_person(r) for r in level3],
        "levels_meta": levels_meta,
    }
