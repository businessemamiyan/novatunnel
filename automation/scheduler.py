import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from shared import db, notify
from telegram_poster import post_scheduled_content as post_to_telegram
from instagram_poster import post_random_package_promo as post_to_instagram_official
from instagram_unofficial import run_forever as instagram_unofficial_loop
from instagram_unofficial import post_random_package_promo as post_to_instagram_unofficial
from instagram_manual_assist import send_instagram_draft
from daily_motivation import send_daily_motivation


def guarded(name, coro_func):
    """خطاهای پیش‌بینی‌نشده در جاب‌های زمان‌بندی‌شده را به گروه هشدار تیم گزارش می‌کند."""
    async def wrapper():
        try:
            await coro_func()
        except Exception as e:
            logging.exception("%s failed unexpectedly", name)
            await notify.notify_team_group(f"🔴 <b>خطای غیرمنتظره در اتوماسیون</b>\n{name}: {e}")
    wrapper.__name__ = name
    return wrapper


async def main():
    logging.basicConfig(level=logging.INFO)
    await db.init_pool()

    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
    for slot in config.POST_TIMES.split(","):
        hour, minute = slot.strip().split(":")
        scheduler.add_job(guarded("post_to_telegram", post_to_telegram), CronTrigger(hour=int(hour), minute=int(minute)))
        if config.INSTAGRAM_ENABLED:
            scheduler.add_job(
                guarded("post_to_instagram_official", post_to_instagram_official),
                CronTrigger(hour=int(hour), minute=int(minute)),
            )
        if config.INSTAGRAM_UNOFFICIAL_ENABLED:
            scheduler.add_job(
                guarded("post_to_instagram_unofficial", post_to_instagram_unofficial),
                CronTrigger(hour=int(hour), minute=int(minute)),
            )
        else:
            # لاگین خودکار اینستاگرام فعلاً با VPNهای در دسترس بلاک می‌شود؛
            # به‌جایش پیش‌نویس آماده برای پست دستی به ادمین‌ها ارسال می‌شود.
            scheduler.add_job(
                guarded("send_instagram_draft", send_instagram_draft),
                CronTrigger(hour=int(hour), minute=int(minute)),
            )
    scheduler.add_job(
        guarded("send_daily_motivation", send_daily_motivation),
        CronTrigger(hour=config.DAILY_MOTIVATION_HOUR, minute=0),
    )

    scheduler.start()
    if config.INSTAGRAM_UNOFFICIAL_ENABLED:
        asyncio.create_task(instagram_unofficial_loop())

    logging.info("automation scheduler started, post times: %s", config.POST_TIMES)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
