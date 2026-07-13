import httpx

from . import config, db

TELEGRAM_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"


async def notify_admins(text: str):
    admin_ids = await db.get_all_active_admin_ids()
    async with httpx.AsyncClient(timeout=15) as client:
        for admin_id in admin_ids:
            try:
                await client.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={"chat_id": admin_id, "text": text, "parse_mode": "HTML"},
                )
            except Exception:
                pass


async def notify_team_group(text: str):
    """اعلان خطاهای فنی (پرداخت، باگ سیستم) به گروه داخلی تیم — اگر تنظیم نشده باشد بی‌صدا رد می‌شود."""
    if not config.TEAM_ALERT_GROUP_CHAT_ID:
        return
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": config.TEAM_ALERT_GROUP_CHAT_ID, "text": text, "parse_mode": "HTML"},
            )
        except Exception:
            pass
