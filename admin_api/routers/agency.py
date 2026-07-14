import json
import re

import asyncpg
import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from shared import config, db, purchase_service
from auth import get_current_admin, get_current_user

router = APIRouter()

TELEGRAM_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,29}$")


class ActivationRequest(BaseModel):
    tier: str


class ResaleRequest(BaseModel):
    customer_telegram_id: int
    volume_gb: float
    price_toman: int
    is_gift_resale: bool = False
    service_label: str | None = None
    is_vip_service: bool = False


class SlugRequest(BaseModel):
    slug: str


class PriceRequest(BaseModel):
    package_id: int
    price_toman: int


class AgentExpenseCreate(BaseModel):
    amount_toman: int
    description: str
    category: str | None = None


class AgentCardCreate(BaseModel):
    card_number: str
    card_holder: str


class AgentCardUpdate(BaseModel):
    card_number: str
    card_holder: str
    is_active: bool


def _serialize_expense(e):
    return {
        "id": str(e["id"]),
        "amount_toman": int(e["amount_toman"]),
        "description": e["description"],
        "category": e["category"],
        "created_at": e["created_at"].isoformat(),
    }


def _serialize_request(r):
    return {
        "id": str(r["id"]),
        "tier": r["tier"],
        "activation_fee_toman": int(r["activation_fee_toman"]),
        "is_upgrade": r["is_upgrade"],
        "status": r["status"],
        "receipt_file_id": r["receipt_file_id"],
        "created_at": r["created_at"].isoformat(),
        "telegram_id": r.get("telegram_id"),
        "telegram_username": r.get("telegram_username"),
        "full_name": r.get("full_name"),
    }


@router.get("/tiers")
async def list_tiers():
    rows = await db.get_agency_tier_config()
    return [dict(r) for r in rows]


@router.get("/me")
async def my_agency_status(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        return {"is_agent": False}

    downline = await db.get_agency_downline(db_user["id"])
    return {
        "is_agent": True,
        "tier": agent["tier"],
        "is_panel_active": agent["is_panel_active"],
        "purchase_rate_toman_per_gb": int(agent["purchase_rate_toman_per_gb"]),
        "min_wallet_balance_toman": int(agent["min_wallet_balance_toman"]),
        "wallet_balance_toman": int(db_user["wallet_balance_toman"]),
        "activated_at": agent["activated_at"].isoformat(),
        "downline_count": len(downline),
        "downline": [{"agent_id": str(d["agent_id"]), "tier": d["tier"], "level": d["level"]} for d in downline],
        "agent_slug": agent["agent_slug"],
        "custom_pricing_enabled": agent["custom_pricing_enabled"],
    }


@router.post("/slug")
async def set_slug(body: SlugRequest, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    slug = body.slug.strip().lower()
    if not SLUG_RE.match(slug):
        raise HTTPException(400, "شناسه باید فقط حروف انگلیسی کوچک، عدد و خط تیره باشد (۳ تا ۳۰ کاراکتر)")

    try:
        updated = await db.set_agent_slug(db_user["id"], slug)
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(409, "این شناسه قبلاً استفاده شده، یک مورد دیگر انتخاب کنید")

    return {"agent_slug": updated["agent_slug"]}


@router.get("/pricing")
async def get_pricing(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    rows = await db.get_agent_plan_pricing(db_user["id"])
    return [
        {
            "package_id": r["package_id"],
            "name": r["name"],
            "volume_gb": float(r["volume_gb"]),
            "default_price_toman": int(r["default_price_toman"]),
            "agent_price_toman": int(r["agent_price_toman"]) if r["agent_price_toman"] is not None else None,
        }
        for r in rows
    ]


@router.post("/pricing")
async def set_pricing(body: PriceRequest, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    try:
        row = await db.set_agent_plan_price(db_user["id"], body.package_id, body.price_toman)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"package_id": row["package_id"], "retail_price_toman": int(row["retail_price_toman"])}


@router.get("/customers")
async def my_customers(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    rows = await db.get_agent_customers(db_user["id"])
    return [
        {
            "id": str(r["id"]),
            "telegram_id": r["telegram_id"],
            "telegram_username": r["telegram_username"],
            "full_name": r["full_name"],
            "volume_gb": float(r["volume_gb"]),
            "price_toman": int(r["price_toman"]),
            "is_gift_resale": r["is_gift_resale"],
            "service_label": r["service_label"],
            "purchased_at": r["purchased_at"].isoformat(),
        }
        for r in rows
    ]


@router.get("/accounting")
async def agent_accounting(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    sales = dict(await db.get_sales_stats_by_scope(db_user["id"]))
    cost = dict(await db.get_wallet_cost_stats(db_user["id"], "agency_resale_cost"))
    expenses = await db.get_expenses(db_user["id"])
    expense_total = int(await db.get_expense_total(db_user["id"]))
    net_profit = int(sales["total_sales"]) - int(cost["total_cost"]) - expense_total

    return {
        "sales": {k: int(v) for k, v in sales.items()},
        "cost": {k: int(v) for k, v in cost.items()},
        "expenses": [_serialize_expense(dict(e)) for e in expenses],
        "expense_total": expense_total,
        "net_profit": net_profit,
    }


@router.post("/accounting/expenses")
async def add_agent_expense(body: AgentExpenseCreate, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    if body.amount_toman <= 0:
        raise HTTPException(400, "مبلغ باید بزرگتر از صفر باشد")
    if not body.description.strip():
        raise HTTPException(400, "توضیح هزینه را وارد کنید")

    e = await db.create_expense(
        body.amount_toman, body.description.strip(), body.category, user["telegram_id"], db_user["id"]
    )
    return _serialize_expense(dict(e))


@router.delete("/accounting/expenses/{expense_id}")
async def remove_agent_expense(expense_id: str, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    await db.delete_expense(expense_id, db_user["id"])
    return {"ok": True}


async def _require_agent(user: dict):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")
    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")
    return db_user


@router.get("/payment-cards")
async def list_agent_cards(user: dict = Depends(get_current_user)):
    db_user = await _require_agent(user)
    rows = await db.get_all_payment_cards(db_user["id"])
    return [dict(r) for r in rows]


@router.post("/payment-cards")
async def create_agent_card(body: AgentCardCreate, user: dict = Depends(get_current_user)):
    db_user = await _require_agent(user)
    card = await db.create_payment_card(body.card_number, body.card_holder, db_user["id"])
    return dict(card)


@router.patch("/payment-cards/{card_id}")
async def update_agent_card(card_id: int, body: AgentCardUpdate, user: dict = Depends(get_current_user)):
    db_user = await _require_agent(user)
    card = await db.update_payment_card(card_id, body.card_number, body.card_holder, body.is_active, db_user["id"])
    if card is None:
        raise HTTPException(404, "not found")
    return dict(card)


@router.delete("/payment-cards/{card_id}")
async def delete_agent_card(card_id: int, user: dict = Depends(get_current_user)):
    db_user = await _require_agent(user)
    await db.delete_payment_card(card_id, db_user["id"])
    return {"ok": True}


@router.post("/activate")
async def request_activation(body: ActivationRequest, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    tier_cfg = await db.get_agency_tier_config_by_tier(body.tier)
    if tier_cfg is None:
        raise HTTPException(400, "رده نامعتبر است")

    existing = await db.get_agent_info(db_user["id"])
    is_upgrade = existing is not None
    fee = int(tier_cfg["activation_fee_toman"])
    if is_upgrade:
        current_cfg = await db.get_agency_tier_config_by_tier(existing["tier"])
        fee = max(fee - int(current_cfg["activation_fee_toman"]), 0)

    upline_agent_id = None
    if db_user["referrer_id"]:
        referrer_agent = await db.get_agent_info(db_user["referrer_id"])
        if referrer_agent:
            upline_agent_id = db_user["referrer_id"]

    req = await db.create_agency_activation_request(db_user["id"], body.tier, fee, upline_agent_id, is_upgrade)
    card_number, card_holder = await purchase_service.get_payment_card()
    return {
        "id": str(req["id"]),
        "tier": req["tier"],
        "activation_fee_toman": int(req["activation_fee_toman"]),
        "is_upgrade": is_upgrade,
        "card_number": card_number,
        "card_holder": card_holder,
        "payment_notice": purchase_service.PAYMENT_SAFETY_NOTICE,
    }


@router.post("/activate/{request_id}/receipt")
async def upload_activation_receipt(request_id: str, file: UploadFile = File(...),
                                     user: dict = Depends(get_current_user)):
    req = await db.get_agency_activation_request(request_id)
    if req is None:
        raise HTTPException(404, "not found")

    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None or req["user_id"] != db_user["id"]:
        raise HTTPException(403, "forbidden")

    photo_bytes = await file.read()
    caption = (
        f"🏷 درخواست فعال‌سازی/ارتقای نمایندگی\n"
        f"کاربر: {db_user['full_name']} (@{user.get('username')}) id={user['telegram_id']}\n"
        f"رده: {req['tier']}\n"
        f"مبلغ: {int(req['activation_fee_toman']):,} تومان\n"
        f"شناسه درخواست: {req['id']}"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ تایید", "callback_data": f"agency_approve:{request_id}"},
            {"text": "❌ رد", "callback_data": f"agency_reject:{request_id}"},
        ]]
    }
    admin_ids = await db.get_all_active_admin_ids()
    file_id = None
    async with httpx.AsyncClient(timeout=30) as client:
        for admin_id in admin_ids:
            resp = await client.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={"chat_id": admin_id, "caption": caption, "reply_markup": json.dumps(keyboard)},
                files={"photo": ("receipt.jpg", photo_bytes, file.content_type or "image/jpeg")},
            )
            result = resp.json()
            if file_id is None and result.get("ok"):
                file_id = result["result"]["photo"][-1]["file_id"]

    if file_id:
        await db.update_agency_activation_receipt(request_id, file_id)
    return {"ok": True}


@router.post("/resell")
async def resell_to_customer(body: ResaleRequest, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "کاربر پیدا نشد")

    agent = await db.get_agent_info(db_user["id"])
    if agent is None:
        raise HTTPException(403, "شما نماینده نیستید")

    customer = await db.get_user_by_telegram_id(body.customer_telegram_id)
    if customer is None:
        raise HTTPException(404, "این کاربر هنوز در ربات ثبت‌نام نکرده است")

    try:
        purchase = await db.create_agent_resale(
            db_user["id"], customer["id"], body.volume_gb, body.price_toman,
            body.is_gift_resale, body.service_label, body.is_vip_service,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    buyer = await db.get_user_by_id(purchase["user_id"])
    try:
        panel_status = await purchase_service.deliver_service_for_purchase(purchase, buyer)
    except Exception as e:
        panel_status = f"⚠️ خطا در ساخت/تمدید پنل Marzban: {e}"

    return {"id": str(purchase["id"]), "panel_status": panel_status}


# ===== admin =====

@router.get("/admin/requests")
async def list_activation_requests(status: str | None = None, limit: int = 50, offset: int = 0,
                                    admin: dict = Depends(get_current_admin)):
    rows = await db.get_agency_activation_requests(status, limit, offset)
    return [_serialize_request(dict(r)) for r in rows]


@router.post("/admin/requests/{request_id}/approve")
async def approve_activation(request_id: str, admin: dict = Depends(get_current_admin)):
    agent = await db.confirm_agency_activation_request(request_id)
    if agent is None:
        raise HTTPException(409, "already processed")

    buyer = await db.get_user_by_id(agent["user_id"])
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": buyer["telegram_id"],
                "text": f"🎉 پنل نمایندگی رده «{agent['tier']}» شما فعال شد!",
            },
        )
    await db.log_admin_action(
        admin["telegram_id"], "agency_activation_approve", f"request {request_id}",
        {"tier": agent["tier"]},
    )
    return {"ok": True}


@router.post("/admin/requests/{request_id}/reject")
async def reject_activation(request_id: str, admin: dict = Depends(get_current_admin)):
    req = await db.reject_agency_activation_request(request_id)
    if req is None:
        raise HTTPException(409, "already processed")

    buyer = await db.get_user_by_id(req["user_id"])
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": buyer["telegram_id"], "text": "❌ درخواست فعال‌سازی نمایندگی شما تایید نشد."},
        )
    await db.log_admin_action(admin["telegram_id"], "agency_activation_reject", f"request {request_id}")
    return {"ok": True}
