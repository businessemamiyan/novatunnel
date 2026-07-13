import datetime

import jdatetime

from . import config


def to_shamsi(dt) -> str:
    if dt is None:
        return "-"
    local = jdatetime.datetime.fromgregorian(datetime=dt)
    return local.strftime("%Y/%m/%d - %H:%M")


def compute_status(panel, marzban_user) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    if panel["expires_at"] and panel["expires_at"] < now:
        return "🔴 منقضی شده"
    if marzban_user:
        limit = marzban_user.get("data_limit")
        used = marzban_user.get("used_traffic") or 0
        if limit and limit > 0 and used / limit >= 0.85:
            return "🟡 رو به اتمام"
    return "🟢 فعال"


def format_service_card(panel, marzban_user, sub_url: str) -> str:
    status = compute_status(panel, marzban_user)
    return (
        "┏━━━━━━━━━━━━━━━━━━━┓\n"
        "      🚀 <b>NovaTunnel</b>\n"
        "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"🔖 <b>سرویس:</b> {panel['label'] or panel['marzban_username']}\n"
        f"🌍 <b>لوکیشن سرور:</b> {config.SERVER_LOCATION}\n"
        f"📊 <b>وضعیت:</b> {status}\n"
        f"🗓 <b>تاریخ خرید:</b> {to_shamsi(panel['created_at'])}\n"
        f"⏳ <b>تاریخ انقضا:</b> {to_shamsi(panel['expires_at'])}\n\n"
        f"🔗 <b>لینک هوشمند اشتراک:</b>\n<code>{sub_url}</code>"
    )
