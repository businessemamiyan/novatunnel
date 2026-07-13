import asyncio
import logging

import httpx

import config
from shared import ai_client, content_generator, db

logger = logging.getLogger(__name__)

BOT_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"

# فاصله کوچک بین ارسال‌ها تا از محدودیت نرخ تلگرام (~۳۰ پیام/ثانیه) عبور نکنیم
SEND_DELAY_SECONDS = 0.05


async def send_daily_motivation():
    try:
        message = await content_generator.generate_motivational_message()
    except ai_client.AINotConfigured:
        logger.warning("CLOUDFLARE_AI_TOKEN not set, skipping daily motivation")
        return
    except Exception:
        logger.exception("failed to generate motivational message")
        return

    user_ids = await db.get_all_user_telegram_ids()
    sent, failed = 0, 0
    async with httpx.AsyncClient(timeout=15) as client:
        for uid in user_ids:
            try:
                r = await client.post(f"{BOT_API}/sendMessage", json={"chat_id": uid, "text": message})
                if r.status_code == 200:
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
            await asyncio.sleep(SEND_DELAY_SECONDS)

    logger.info("daily motivation sent: %d ok, %d failed (of %d)", sent, failed, len(user_ids))
