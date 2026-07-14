import datetime
import json

import httpx

from . import config, db, marzban, notify, qr, service_card

TELEGRAM_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"

GUIDE_BUTTON_MARKUP = {
    "inline_keyboard": [[{"text": "📖 راهنمای اتصال", "callback_data": "guide"}]]
}

PAYMENT_SAFETY_NOTICE = (
    "⚠️ در توضیحات واریز یا یادداشت تراکنش، به هیچ‌وجه از کلماتی مثل «فیلترشکن»، «VPN» "
    "یا هر عبارت مشابه استفاده نکنید."
)


async def get_payment_card(agent_id=None) -> tuple[str, str]:
    """یکی از کارت‌های فعال را تصادفی برمی‌گرداند تا حجم تراکنش‌ها بین چند کارت پخش شود.
    اگر agent_id داده شود (مشتری متصل به نماینده از طریق لینک اختصاصی)، پول باید مستقیم به کارت خودِ
    نماینده برود، نه مالک — اگر آن نماینده هنوز کارتی ثبت نکرده باشد، به کارت‌های مالک برمی‌گردیم."""
    if agent_id:
        card = await db.get_random_payment_card(agent_id)
        if card:
            return card["card_number"], card["card_holder"]

    card = await db.get_random_payment_card()
    if card:
        return card["card_number"], card["card_holder"]
    return config.CARD_NUMBER, config.CARD_HOLDER


async def _send_telegram_message(chat_id, text: str, reply_markup: dict | None = None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)


async def _send_telegram_photo_bytes(chat_id, photo_bytes: bytes, caption: str,
                                      reply_markup: dict | None = None):
    data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    files = {"photo": ("novatunnel_qr.png", photo_bytes, "image/png")}
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data=data, files=files)


async def deliver_service_for_purchase(purchase, buyer) -> str:
    """می‌سازد یا تمدید می‌کند اکانت Marzban متناظر با این خرید و QR+کانفیگ را برای خریدار می‌فرستد.
    این تابع منبع واحد این منطق است — هم ربات هم پنل ادمین Mini App همین را صدا می‌زنند."""
    volume_gb = float(purchase["volume_gb"])
    now = datetime.datetime.now(datetime.timezone.utc)

    if purchase["renewed_panel_id"]:
        panel = await db.get_panel(purchase["renewed_panel_id"])
        base = panel["expires_at"] if panel["expires_at"] and panel["expires_at"] > now else now
        new_expires_at = base + datetime.timedelta(days=config.SERVICE_VALIDITY_DAYS)
        marzban_user = await marzban.renew_service(
            panel["marzban_username"], volume_gb, int(new_expires_at.timestamp())
        )
        await db.renew_panel(panel["id"], volume_gb, new_expires_at)
        panel = await db.get_panel(panel["id"])
    else:
        expires_at = now + datetime.timedelta(days=config.SERVICE_VALIDITY_DAYS)
        is_vip = False
        if purchase["package_id"]:
            package = await db.get_package(purchase["package_id"])
            is_vip = bool(package and package["is_vip"])
        username, marzban_user = await marzban.create_new_service(
            buyer["telegram_id"], volume_gb, int(expires_at.timestamp()), is_vip=is_vip
        )
        panel = await db.create_panel(
            buyer["id"], purchase["id"], username, purchase["service_label"],
            volume_gb, expires_at,
        )

    sub_url = marzban.subscription_url(marzban_user)
    card_text = service_card.format_service_card(panel, marzban_user, sub_url)
    qr_bytes = qr.generate_branded_qr(sub_url).read()

    await _send_telegram_photo_bytes(
        buyer["telegram_id"], qr_bytes, f"✅ پرداخت شما تایید شد!\n\n{card_text}",
        reply_markup=GUIDE_BUTTON_MARKUP,
    )
    return "✅ پنل ساخته/تمدید و کانفیگ ارسال شد."


async def approve_purchase(purchase_id: str, admin_telegram_id: int):
    """تایید پرداخت: هم از ربات (فوروارد رسید) هم از Mini App صدا زده می‌شود."""
    purchase = await db.confirm_purchase(purchase_id)
    if purchase is None:
        return None

    rewards = await db.apply_referral_rewards(purchase)
    buyer = await db.get_user_by_id(purchase["user_id"])

    wallet_used = float(purchase["wallet_credit_used_toman"] or 0)
    if wallet_used > 0:
        await db.credit_wallet(
            buyer["id"], "purchase_debit", -wallet_used,
            note="استفاده از موجودی کیف‌پول در خرید", reference_purchase_id=purchase["id"],
        )

    reward_credit_used = float(purchase["reward_credit_used_toman"] or 0)
    if reward_credit_used > 0:
        await db.debit_reward_credit(buyer["id"], reward_credit_used)

    if purchase["package_id"]:
        package = await db.get_package(purchase["package_id"])
        if package and package["is_key_panel"]:
            await db.convert_gift_to_reward_credit_standalone(buyer["id"])

    # خرید خودسرویس مشتریِ متصل به نماینده (از طریق لینک اختصاصی) — هزینه خودکار از کیف‌پول نماینده کسر می‌شود
    if purchase["seller_type"] == "agent" and purchase["seller_agent_id"]:
        agent_id = purchase["seller_agent_id"]
        agent = await db.get_agent_info(agent_id)
        if agent:
            volume_gb = float(purchase["volume_gb"])
            cost = volume_gb * float(agent["purchase_rate_toman_per_gb"])
            profit = float(purchase["price_toman"]) - cost
            await db.credit_wallet(
                agent_id, "agency_resale_cost", -cost,
                note=f"هزینه فروش خودکار از طریق لینک نماینده به کاربر {buyer['telegram_id']}",
                reference_purchase_id=purchase["id"],
            )
            await db.apply_agency_chain_reward_standalone(agent_id, volume_gb)
            agent_user = await db.get_user_by_id(agent_id)
            await _send_telegram_message(
                agent_user["telegram_id"],
                f"🎉 فروش جدید از طریق لینک اختصاصی‌تان!\n"
                f"مشتری: {buyer['full_name']}\n"
                f"حجم: {volume_gb:g} گیگ — سود شما: {profit:,.0f} تومان",
            )

    try:
        panel_status = await deliver_service_for_purchase(purchase, buyer)
    except Exception as e:
        await _send_telegram_message(
            buyer["telegram_id"],
            "✅ پرداخت شما تایید شد! پنل شما در حال آماده‌سازی است، کمی صبر کنید."
        )
        panel_status = f"⚠️ خطا در ساخت/تمدید پنل Marzban: {e}"
        await notify.notify_team_group(
            f"🔴 <b>خطا در تحویل سرویس</b>\n"
            f"خرید: {purchase_id}\n"
            f"خریدار: {buyer['telegram_id']}\n"
            f"خطا: {e}"
        )

    await db.log_admin_action(
        admin_telegram_id, "receipt_approve", f"purchase {purchase_id}",
        {"panel_status": panel_status, "rewards_count": len(rewards)},
    )
    return {"purchase": purchase, "panel_status": panel_status, "rewards": rewards}


async def reject_purchase_service(purchase_id: str, admin_telegram_id: int):
    purchase = await db.reject_purchase(purchase_id)
    if purchase is None:
        return None
    buyer = await db.get_user_by_id(purchase["user_id"])
    await _send_telegram_message(
        buyer["telegram_id"], "❌ پرداخت شما تایید نشد. لطفاً از طریق پشتیبانی پیگیری کنید."
    )
    await db.log_admin_action(admin_telegram_id, "receipt_reject", f"purchase {purchase_id}")
    return purchase
