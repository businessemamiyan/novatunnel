from aiogram import Router, F
from aiogram.types import Message

from shared import db, service_card

router = Router()

STATUS_LABELS = {
    "pending": "⏳ در انتظار تایید",
    "confirmed": "✅ موفق",
    "failed": "❌ ناموفق",
    "refunded": "↩️ بازگشت‌شده",
}


@router.message(F.text == "👛 کیف پول")
async def show_wallet(message: Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("لطفاً ابتدا دستور /start را بزنید.")
        return

    purchases = await db.get_purchases_for_user(user["id"])

    text = (
        "┏━━━━━━━━━━━━━━━━━━━┓\n"
        "      👛 <b>کیف پول</b>\n"
        "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"💰 موجودی کیف‌پول: {int(user['wallet_balance_toman']):,} تومان\n\n"
        "🧾 <b>تاریخچه خریدها:</b>\n"
    )

    if not purchases:
        text += "\nهنوز خریدی ثبت نشده است."
    else:
        for p in purchases:
            status = STATUS_LABELS.get(p["payment_status"], p["payment_status"])
            date = service_card.to_shamsi(p["purchased_at"])
            text += (
                f"\n▫️ {p['package_name'] or '-'} — {int(p['price_toman']):,} تومان\n"
                f"   {status} · {date}\n"
            )

    await message.answer(text)
