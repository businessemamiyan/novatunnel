import datetime
import json

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from shared import config, db, purchase_service, zarinpal
from auth import get_current_user

router = APIRouter()

TELEGRAM_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"

RESULT_PAGE = """<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>نتیجه پرداخت</title>
<style>
body{{font-family:Tahoma,sans-serif;background:#0b0f1a;color:#e8ecf4;display:flex;
align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center}}
.card{{background:#141a2a;border-radius:16px;padding:32px 24px;max-width:360px}}
.icon{{font-size:48px;margin-bottom:12px}}
a{{color:#4ade80;text-decoration:none}}
</style></head>
<body><div class="card"><div class="icon">{icon}</div><h3>{title}</h3><p>{message}</p>
<p><a href="https://t.me/Milivpnvipbot">بازگشت به ربات</a></p></div></body></html>"""


class PurchaseCreate(BaseModel):
    package_id: int
    service_label: str | None = None
    discount_code: str | None = None
    renewed_panel_id: str | None = None


@router.post("")
async def create_purchase(body: PurchaseCreate, user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None:
        raise HTTPException(404, "user not found")

    package = await db.get_package(body.package_id)
    if package is None or not package["is_active"]:
        raise HTTPException(404, "package not found")

    if package["is_key_panel"] and not await db.can_purchase_key_panel(db_user["id"], db_user["gift_balance_gb"]):
        raise HTTPException(403, "پنل کلید فقط برای کاربرانی است که حجم هدیه دارند ولی سرویس فعالی ندارند")

    if body.renewed_panel_id:
        panel = await db.get_panel(body.renewed_panel_id)
        if panel is None or panel["user_id"] != db_user["id"]:
            raise HTTPException(403, "forbidden")

    agent_pricing = await db.get_agent_pricing_for_customer(db_user["id"])
    price = int(agent_pricing.get(package["id"], package["retail_price_toman"]))
    discount_amount = 0
    discount_code_id = None

    if body.discount_code:
        discount = await db.find_discount_code(body.discount_code)
        if discount is None:
            raise HTTPException(400, "کد تخفیف نامعتبر است")
        if discount["expires_at"] and discount["expires_at"] < datetime.datetime.now(datetime.timezone.utc):
            raise HTTPException(400, "این کد تخفیف منقضی شده است")
        if discount["max_uses"] is not None and discount["used_count"] >= discount["max_uses"]:
            raise HTTPException(400, "ظرفیت این کد تخفیف تمام شده است")
        if await db.user_used_discount_code(discount["id"], db_user["id"]):
            raise HTTPException(400, "شما قبلاً از این کد تخفیف استفاده کرده‌اید")
        if price < int(discount["min_purchase_toman"]):
            raise HTTPException(400, "مبلغ این بسته کمتر از حداقل خرید مجاز این کد است")
        discount_code_id = discount["id"]
        discount_amount = db.compute_discount_amount(discount, price)

    final_price = price - discount_amount

    reward_credit_used = 0
    if final_price > 0:
        reward_credit_balance = float(db_user["reward_credit_toman"])
        if reward_credit_balance > 0:
            reward_credit_used = min(reward_credit_balance, final_price)
            final_price -= reward_credit_used

    wallet_used = 0
    if final_price > 0:
        wallet_balance = int(db_user["wallet_balance_toman"])
        if wallet_balance > 0:
            wallet_used = min(wallet_balance, final_price)
            final_price -= wallet_used

    binding = await db.get_customer_agent_binding(db_user["id"])
    purchase = await db.create_pending_purchase(
        db_user["id"], package["id"], package["volume_gb"], final_price,
        discount_code_id=discount_code_id, discount_amount_toman=discount_amount,
        service_label=body.service_label, renewed_panel_id=body.renewed_panel_id,
        wallet_credit_used_toman=wallet_used, reward_credit_used_toman=reward_credit_used,
        seller_agent_id=binding["agent_id"] if binding else None,
    )

    if final_price <= 0:
        await purchase_service.approve_purchase(purchase["id"], user["telegram_id"])
        return {"id": str(purchase["id"]), "status": "auto_approved", "final_price": 0}

    card_number, card_holder = await purchase_service.get_payment_card()
    return {
        "id": str(purchase["id"]),
        "status": "awaiting_receipt",
        "final_price": final_price,
        "discount_amount": discount_amount,
        "wallet_used": wallet_used,
        "reward_credit_used": reward_credit_used,
        "card_number": card_number,
        "card_holder": card_holder,
        "payment_notice": purchase_service.PAYMENT_SAFETY_NOTICE,
    }


@router.post("/{purchase_id}/pay-online")
async def pay_online(purchase_id: str, user: dict = Depends(get_current_user)):
    if not zarinpal.is_configured():
        raise HTTPException(400, "پرداخت آنلاین در حال حاضر فعال نیست")

    purchase = await db.get_purchase(purchase_id)
    if purchase is None:
        raise HTTPException(404, "not found")

    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None or purchase["user_id"] != db_user["id"]:
        raise HTTPException(403, "forbidden")
    if purchase["payment_status"] != "pending":
        raise HTTPException(409, "این خرید قبلاً پردازش شده است")

    amount = int(purchase["price_toman"])
    try:
        authority = await zarinpal.request_payment(
            amount, f"خرید سرویس NovaTunnel - {purchase_id}", "/api/purchases/zarinpal-callback"
        )
    except zarinpal.ZarinpalError as e:
        raise HTTPException(502, str(e))

    await db.set_purchase_gateway_authority(purchase_id, authority)
    return {"payment_url": zarinpal.payment_url(authority)}


@router.get("/zarinpal-callback")
async def zarinpal_callback(request: Request):
    authority = request.query_params.get("Authority")
    status = request.query_params.get("Status")

    purchase = await db.get_purchase_by_authority(authority) if authority else None
    if purchase is None:
        return HTMLResponse(RESULT_PAGE.format(icon="⚠️", title="یافت نشد", message="این تراکنش یافت نشد."))

    if status != "OK":
        return HTMLResponse(RESULT_PAGE.format(icon="❌", title="پرداخت لغو شد", message="پرداخت توسط شما لغو شد."))

    if purchase["payment_status"] != "pending":
        return HTMLResponse(RESULT_PAGE.format(icon="✅", title="قبلاً پردازش شده", message="این پرداخت قبلاً تایید شده است."))

    try:
        await zarinpal.verify_payment(int(purchase["price_toman"]), authority)
    except zarinpal.ZarinpalError as e:
        return HTMLResponse(RESULT_PAGE.format(icon="❌", title="پرداخت ناموفق", message=str(e)))

    buyer = await db.get_user_by_id(purchase["user_id"])
    await purchase_service.approve_purchase(purchase["id"], buyer["telegram_id"])
    return HTMLResponse(RESULT_PAGE.format(
        icon="✅", title="پرداخت موفق", message="سرویس شما در حال آماده‌سازی است و به‌زودی در ربات ارسال می‌شود."
    ))


@router.post("/{purchase_id}/receipt")
async def upload_purchase_receipt(purchase_id: str, file: UploadFile = File(...),
                                   user: dict = Depends(get_current_user)):
    purchase = await db.get_purchase(purchase_id)
    if purchase is None:
        raise HTTPException(404, "not found")

    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None or purchase["user_id"] != db_user["id"]:
        raise HTTPException(403, "forbidden")

    package = await db.get_package(purchase["package_id"]) if purchase["package_id"] else None
    photo_bytes = await file.read()
    caption = (
        f"🧾 رسید پرداخت جدید (از Mini App)\n"
        f"کاربر: {db_user['full_name']} (@{user.get('username')}) id={user['telegram_id']}\n"
        f"سرویس: {purchase['service_label'] or '(تمدید سرویس موجود)'}\n"
        f"بسته: {package['name'] if package else '-'}\n"
        f"مبلغ: {int(purchase['price_toman']):,} تومان\n"
        f"شناسه خرید: {purchase['id']}"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ تایید پرداخت", "callback_data": f"approve:{purchase_id}"},
            {"text": "❌ رد کردن", "callback_data": f"reject:{purchase_id}"},
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
        await db.update_purchase_receipt_file_id(purchase_id, file_id)
    return {"ok": True}
