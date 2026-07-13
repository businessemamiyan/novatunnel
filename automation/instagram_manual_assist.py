import logging
import random

import httpx

import config
from shared import ai_client, content_generator, db, promo_image
from telegram_poster import get_bot_username

logger = logging.getLogger(__name__)

BOT_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"


async def _send_photo_to_admin(admin_id: int, image_bytes: bytes, caption: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BOT_API}/sendPhoto",
            data={"chat_id": admin_id, "caption": caption},
            files={"photo": ("promo.png", image_bytes, "image/png")},
        )
        r.raise_for_status()


async def send_instagram_draft():
    """چون لاگین خودکار اینستاگرام (روش غیررسمی) با VPNهای در دسترس بلاک می‌شود،
    به‌جایش محتوا و عکس آماده را برای ادمین‌ها می‌فرستد تا دستی از اپ رسمی پست کنند."""
    packages = await db.get_active_packages()
    if not packages:
        return
    package = random.choice(packages)

    try:
        bot_username = await get_bot_username()
        content = await content_generator.generate_post_content(package, bot_username, "instagram")
    except ai_client.AINotConfigured:
        logger.warning("CLOUDFLARE_AI_TOKEN not set, skipping instagram draft generation")
        return
    except Exception:
        logger.exception("failed to generate instagram draft content")
        return

    await db.create_generated_post("instagram", content["caption"])

    try:
        image_bytes = promo_image.generate_promo_image(
            content["headline"], content["price_line"], content["subtitle"], content.get("cta")
        ).getvalue()
        note = (
            "📸 پیش‌نویس پست اینستاگرام آماده شد — لطفاً همین عکس و متن رو دستی تو اینستاگرام پست کنید:\n\n"
            f"{content['caption']}"
        )
        admin_ids = await db.get_all_active_admin_ids()
        for admin_id in admin_ids:
            await _send_photo_to_admin(admin_id, image_bytes, note)
        logger.info("sent instagram draft for package %s to admins", package["name"])
    except Exception:
        logger.exception("failed to send instagram draft to admins")
