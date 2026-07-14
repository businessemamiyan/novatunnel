import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram import F, Router
from aiogram.types import Message

import config
from shared import db, marzban, notify
from handlers import start, menu, purchase, admin, admin_panel, support, services, wallet, smart_chat, agent_approval

# ثبت اول از همه تا هیچ روتر/فیلتر دیگری (مثل IsAdmin() در روترهای ادمین) قبل از آن پیام Contact را نبیند
priority_contact_router = Router()


@priority_contact_router.message(F.contact)
async def priority_receive_phone_contact(message: Message):
    await menu.receive_phone_contact(message)

EXPIRY_CHECK_INTERVAL_SECONDS = 1800
USAGE_SYNC_INTERVAL_SECONDS = 1800
TRIAL_CLEANUP_INTERVAL_SECONDS = 300


async def expiry_warning_loop(bot: Bot):
    while True:
        try:
            panels = await db.get_panels_needing_expiry_warning()
            for panel in panels:
                try:
                    await bot.send_message(
                        panel["telegram_id"],
                        f"⏳ سرویس «{panel['label'] or panel['marzban_username']}» شما "
                        f"کمتر از ۲۴ ساعت دیگر منقضی می‌شود.\n"
                        f"برای جلوگیری از قطعی، از منوی «🧩 مدیریت سرویس‌ها» تمدید کنید.",
                    )
                finally:
                    await db.mark_expiry_warned(panel["id"])
        except Exception as e:
            logging.exception("expiry_warning_loop error")
            await notify.notify_team_group(f"🔴 <b>خطای غیرمنتظره در ربات</b>\nexpiry_warning_loop: {e}")
        await asyncio.sleep(EXPIRY_CHECK_INTERVAL_SECONDS)


async def usage_sync_loop():
    while True:
        try:
            panels = await db.get_all_active_panels_for_sync()
            if panels:
                marzban_users = await marzban.get_all_users()
                usage_by_username = {u["username"]: (u.get("used_traffic") or 0) for u in marzban_users}
                for panel in panels:
                    used_bytes = usage_by_username.get(panel["marzban_username"])
                    if used_bytes is not None:
                        await db.update_panel_usage(panel["id"], used_bytes / (1024 ** 3))
        except Exception as e:
            logging.exception("usage_sync_loop error")
            await notify.notify_team_group(f"🔴 <b>خطای غیرمنتظره در ربات</b>\nusage_sync_loop: {e}")
        await asyncio.sleep(USAGE_SYNC_INTERVAL_SECONDS)


async def trial_cleanup_loop(bot: Bot):
    """پنل‌های بسته آزمایشی که منقضی شده‌اند را واقعاً از Marzban حذف می‌کند (نه فقط غیرفعال)."""
    while True:
        try:
            panels = await db.get_expired_trial_panels()
            for panel in panels:
                try:
                    await marzban.delete_service(panel["marzban_username"])
                except Exception:
                    pass
                await db.deactivate_panel(panel["id"])
                try:
                    user = await db.get_user_by_id(panel["user_id"])
                    if user:
                        await bot.send_message(
                            user["telegram_id"],
                            "⏳ زمان سرویس آزمایشی شما تمام شد و پاک شد. برای ادامه استفاده، یکی از بسته‌ها رو تهیه کن.",
                        )
                except Exception:
                    pass
        except Exception as e:
            logging.exception("trial_cleanup_loop error")
            await notify.notify_team_group(f"🔴 <b>خطای غیرمنتظره در ربات</b>\ntrial_cleanup_loop: {e}")
        await asyncio.sleep(TRIAL_CLEANUP_INTERVAL_SECONDS)


async def main():
    logging.basicConfig(level=logging.INFO)
    await db.init_pool()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(priority_contact_router)
    dp.include_router(admin.router)
    dp.include_router(agent_approval.router)
    dp.include_router(admin_panel.router)
    dp.include_router(support.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(services.router)
    dp.include_router(wallet.router)
    dp.include_router(purchase.router)
    dp.include_router(smart_chat.router)

    asyncio.create_task(expiry_warning_loop(bot))
    asyncio.create_task(usage_sync_loop())
    asyncio.create_task(trial_cleanup_loop(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
