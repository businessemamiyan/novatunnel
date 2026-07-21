import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class GiftGrant(BaseModel):
    amount_gb: float
    note: str | None = None


def _serialize(u):
    return {
        "id": str(u["id"]),
        "telegram_id": u["telegram_id"],
        "telegram_username": u["telegram_username"],
        "full_name": u["full_name"],
        "phone_number": u["phone_number"],
        "phone_verified": u["phone_verified"],
        "wallet_balance_toman": float(u["wallet_balance_toman"]),
        "gift_balance_gb": float(u["gift_balance_gb"]),
        "last_purchase_at": u["last_purchase_at"].isoformat() if u["last_purchase_at"] else None,
        "created_at": u["created_at"].isoformat(),
    }


@router.get("")
async def list_customers(search: str | None = None, limit: int = 50, offset: int = 0,
                          admin: dict = Depends(get_current_admin)):
    rows = await db.get_all_users_admin(search, limit, offset)
    total = await db.count_all_users(search)
    return {"total": total, "items": [_serialize(u) for u in rows]}


@router.get("/export")
async def export_customers(admin: dict = Depends(get_current_admin)):
    rows = await db.get_all_users_for_export()

    wb = Workbook()
    ws = wb.active
    ws.title = "Customers"
    ws.append([
        "Telegram ID", "Username", "Full Name", "Phone", "Phone Verified",
        "Wallet Balance (Toman)", "Gift Balance (GB)", "Last Purchase", "Registered At",
    ])
    for u in rows:
        ws.append([
            u["telegram_id"],
            u["telegram_username"] or "",
            u["full_name"] or "",
            u["phone_number"] or "",
            "Yes" if u["phone_verified"] else "No",
            float(u["wallet_balance_toman"]),
            float(u["gift_balance_gb"]),
            u["last_purchase_at"].strftime("%Y-%m-%d %H:%M") if u["last_purchase_at"] else "",
            u["created_at"].strftime("%Y-%m-%d %H:%M"),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    await db.log_admin_action(admin["telegram_id"], "panel_customers_export", None, {"count": len(rows)})

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=novatunnel_customers.xlsx"},
    )


@router.get("/{user_id}")
async def customer_detail(user_id: str, admin: dict = Depends(get_current_admin)):
    user = await db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    panels = await db.get_panels_for_user(user_id, active_only=False)
    direct_referrals = await db.get_direct_referrals(user_id)
    agent = await db.get_agent_info(user_id)

    return {
        **_serialize(user),
        "is_agent": agent is not None,
        "agent_tier": agent["tier"] if agent else None,
        "direct_referrals_count": len(direct_referrals),
        "services": [
            {
                "id": str(p["id"]),
                "label": p["label"] or p["marzban_username"],
                "is_active": p["is_active"],
                "traffic_limit_gb": float(p["traffic_limit_gb"]) if p["traffic_limit_gb"] else 0,
                "traffic_used_gb": float(p["traffic_used_gb"]) if p["traffic_used_gb"] else 0,
                "expires_at": p["expires_at"].isoformat() if p["expires_at"] else None,
            }
            for p in panels
        ],
    }


@router.post("/{user_id}/grant-gift")
async def grant_gift(user_id: str, body: GiftGrant, admin: dict = Depends(get_current_admin)):
    if body.amount_gb <= 0:
        raise HTTPException(400, "مقدار باید مثبت باشد")
    user = await db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    await db.admin_grant_gift_volume(user_id, body.amount_gb, admin["telegram_id"], note=body.note)
    await db.log_admin_action(
        admin["telegram_id"], "panel_gift_grant", f"user {user_id}",
        {"amount_gb": body.amount_gb, "note": body.note},
    )
    return {"ok": True}
