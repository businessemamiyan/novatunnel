import json

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from shared import config, db, purchase_service, zarinpal
from auth import get_current_admin, get_current_user

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


class TopupCreate(BaseModel):
    amount_toman: int


@router.post("")
async def create_topup(body: TopupCreate, user: dict = Depends(get_current_user)):
    if body.amount_toman <= 0:
        raise HTTPException(400, "invalid amount")
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    topup = await db.create_wallet_topup_request(db_user["id"], body.amount_toman)
    card_number, card_holder = await purchase_service.get_payment_card()
    return {
        "id": str(topup["id"]),
        "amount_toman": int(topup["amount_toman"]),
        "card_number": card_number,
        "card_holder": card_holder,
        "payment_notice": purchase_service.PAYMENT_SAFETY_NOTICE,
    }


@router.get("/mine")
async def my_topups(user: dict = Depends(get_current_user)):
    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    rows = await db.get_wallet_topup_requests_for_user(db_user["id"])
    return [dict(r) for r in rows]


@router.post("/{topup_id}/pay-online")
async def pay_online_topup(topup_id: str, user: dict = Depends(get_current_user)):
    if not zarinpal.is_configured():
        raise HTTPException(400, "پرداخت آنلاین در حال حاضر فعال نیست")

    topup = await db.get_wallet_topup(topup_id)
    if topup is None:
        raise HTTPException(404, "not found")

    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if db_user is None or topup["user_id"] != db_user["id"]:
        raise HTTPException(403, "forbidden")
    if topup["status"] != "pending":
        raise HTTPException(409, "این درخواست قبلاً پردازش شده است")

    amount = int(topup["amount_toman"])
    try:
        authority = await zarinpal.request_payment(
            amount, f"شارژ کیف‌پول NovaTunnel - {topup_id}", "/api/wallet-topup/zarinpal-callback"
        )
    except zarinpal.ZarinpalError as e:
        raise HTTPException(502, str(e))

    await db.set_wallet_topup_gateway_authority(topup_id, authority)
    return {"payment_url": zarinpal.payment_url(authority)}


@router.get("/zarinpal-callback")
async def zarinpal_callback_topup(request: Request):
    authority = request.query_params.get("Authority")
    status = request.query_params.get("Status")

    topup = await db.get_wallet_topup_by_authority(authority) if authority else None
    if topup is None:
        return HTMLResponse(RESULT_PAGE.format(icon="⚠️", title="یافت نشد", message="این تراکنش یافت نشد."))

    if status != "OK":
        return HTMLResponse(RESULT_PAGE.format(icon="❌", title="پرداخت لغو شد", message="پرداخت توسط شما لغو شد."))

    if topup["status"] != "pending":
        return HTMLResponse(RESULT_PAGE.format(icon="✅", title="قبلاً پردازش شده", message="این پرداخت قبلاً تایید شده است."))

    try:
        await zarinpal.verify_payment(int(topup["amount_toman"]), authority)
    except zarinpal.ZarinpalError as e:
        return HTMLResponse(RESULT_PAGE.format(icon="❌", title="پرداخت ناموفق", message=str(e)))

    confirmed = await db.confirm_wallet_topup(topup["id"])
    if confirmed is None:
        return HTMLResponse(RESULT_PAGE.format(icon="✅", title="قبلاً پردازش شده", message="این پرداخت قبلاً تایید شده است."))

    return HTMLResponse(RESULT_PAGE.format(
        icon="✅", title="شارژ موفق",
        message=f"مبلغ {int(topup['amount_toman']):,} تومان به کیف‌پول شما اضافه شد."
    ))


@router.post("/{topup_id}/receipt")
async def upload_receipt(topup_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    topup = await db.get_wallet_topup(topup_id)
    if topup is None:
        raise HTTPException(404, "not found")

    db_user = await db.get_user_by_telegram_id(user["telegram_id"])
    if topup["user_id"] != db_user["id"]:
        raise HTTPException(403, "forbidden")

    photo_bytes = await file.read()
    caption = (
        f"🧾 درخواست شارژ کیف‌پول (از Mini App)\n"
        f"کاربر: {db_user['full_name']} (@{user.get('username')}) id={user['telegram_id']}\n"
        f"مبلغ: {int(topup['amount_toman']):,} تومان\n"
        f"شناسه درخواست: {topup['id']}"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ تایید", "callback_data": f"wtopup_approve:{topup_id}"},
            {"text": "❌ رد", "callback_data": f"wtopup_reject:{topup_id}"},
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
        await db.update_wallet_topup_receipt_file_id(topup_id, file_id)
    return {"ok": True}


@router.get("/admin")
async def list_topups_admin(status: str | None = None, limit: int = 50, offset: int = 0,
                             admin: dict = Depends(get_current_admin)):
    rows = await db.get_wallet_topup_requests(status, limit, offset)
    return [dict(r) for r in rows]


@router.post("/{topup_id}/approve")
async def approve_topup(topup_id: str, admin: dict = Depends(get_current_admin)):
    topup = await db.confirm_wallet_topup(topup_id)
    if topup is None:
        raise HTTPException(409, "already processed")
    buyer = await db.get_user_by_id(topup["user_id"])
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": buyer["telegram_id"],
                "text": f"✅ شارژ کیف‌پول شما به مبلغ {int(topup['amount_toman']):,} تومان تایید شد.",
            },
        )
    await db.log_admin_action(
        admin["telegram_id"], "wallet_topup_approve", f"topup {topup_id}",
        {"amount_toman": int(topup["amount_toman"])},
    )
    return {"ok": True}


@router.post("/{topup_id}/reject")
async def reject_topup(topup_id: str, admin: dict = Depends(get_current_admin)):
    topup = await db.reject_wallet_topup(topup_id)
    if topup is None:
        raise HTTPException(409, "already processed")
    buyer = await db.get_user_by_id(topup["user_id"])
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": buyer["telegram_id"], "text": "❌ درخواست شارژ کیف‌پول شما تایید نشد."},
        )
    await db.log_admin_action(admin["telegram_id"], "wallet_topup_reject", f"topup {topup_id}")
    return {"ok": True}
