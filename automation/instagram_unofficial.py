import asyncio
import logging
import os
import random
import tempfile
from pathlib import Path

from instagrapi import Client
from PIL import Image

import config
from shared import ai_client, content_generator, db, promo_image, smart_reply
from telegram_poster import get_bot_username

logger = logging.getLogger(__name__)

SESSION_FILE = "/opt/novatunnel-automation/ig_session.json"

# فاصله بین دورهای بررسی و تاخیر قبل از پاسخ، تصادفی و شبیه رفتار انسانی —
# برای کاهش ریسک محدودسازی/بن شدن حساب اینستاگرام (روش غیررسمی).
MIN_POLL_INTERVAL_SECONDS = 240
MAX_POLL_INTERVAL_SECONDS = 600
MIN_REPLY_DELAY_SECONDS = 15
MAX_REPLY_DELAY_SECONDS = 90

_client: Client | None = None


def _has_credentials() -> bool:
    return os.path.exists(SESSION_FILE)


def _get_client() -> Client:
    """فقط از session ذخیره‌شده (گرفته‌شده با login_by_sessionid از مرورگر) استفاده می‌کند —
    هیچ تماسی با endpoint لاگین با رمز عبور نمی‌زند، چون آن مسیر برای اکانت‌های واقعی مسدود است.
    اگر session نامعتبر شود، باید یک‌بار دیگر sessionid تازه از مرورگر گرفته و جایگزین شود."""
    global _client
    if _client is not None:
        return _client
    if not os.path.exists(SESSION_FILE):
        raise RuntimeError("فایل session اینستاگرام موجود نیست.")

    cl = Client()
    cl.load_settings(SESSION_FILE)
    _client = cl
    return cl


async def _handle_direct_messages(cl: Client):
    threads = await asyncio.to_thread(cl.direct_threads, 20)
    for thread in threads:
        for msg in reversed(thread.messages[:5]):
            if msg.user_id == cl.user_id:
                continue
            item_id = f"dm:{msg.id}"
            if await db.is_instagram_item_handled(item_id):
                continue

            text = (msg.text or "").strip()
            if not text:
                await db.mark_instagram_item_handled(item_id, "dm")
                continue

            result = await smart_reply.handle_incoming_message(
                platform="instagram_dm",
                external_user_id=str(msg.user_id),
                external_username=None,
                message_text=text,
            )
            if result["action"] == "reply":
                await asyncio.sleep(random.uniform(MIN_REPLY_DELAY_SECONDS, MAX_REPLY_DELAY_SECONDS))
                await asyncio.to_thread(cl.direct_send, result["text"], thread_ids=[thread.id])
            await db.mark_instagram_item_handled(item_id, "dm")


async def _handle_comments(cl: Client):
    medias = await asyncio.to_thread(cl.user_medias, cl.user_id, 5)
    for media in medias:
        comments = await asyncio.to_thread(cl.media_comments, media.id)
        for comment in comments:
            if comment.user.pk == cl.user_id:
                continue
            item_id = f"comment:{comment.pk}"
            if await db.is_instagram_item_handled(item_id):
                continue

            result = await smart_reply.handle_incoming_message(
                platform="instagram_comment",
                external_user_id=str(comment.user.pk),
                external_username=comment.user.username,
                message_text=comment.text or "",
            )
            if result["action"] == "reply":
                await asyncio.sleep(random.uniform(MIN_REPLY_DELAY_SECONDS, MAX_REPLY_DELAY_SECONDS))
                await asyncio.to_thread(
                    cl.media_comment, media.id, result["text"], comment.pk
                )
            await db.mark_instagram_item_handled(item_id, "comment")


async def post_random_package_promo():
    if not config.INSTAGRAM_UNOFFICIAL_ENABLED or not _has_credentials():
        return

    packages = await db.get_active_packages()
    if not packages:
        return
    package = random.choice(packages)

    try:
        bot_username = await get_bot_username()
        content = await content_generator.generate_post_content(package, bot_username, "instagram")
    except ai_client.AINotConfigured:
        logger.warning("CLOUDFLARE_AI_TOKEN not set, skipping instagram content generation")
        return
    except Exception:
        logger.exception("failed to generate instagram post content")
        return

    post = await db.create_generated_post("instagram", content["caption"])

    tmp_path = None
    try:
        image_buf = promo_image.generate_promo_image(
            content["headline"], content["price_line"], content["subtitle"], content.get("cta")
        )
        img = Image.open(image_buf).convert("RGB")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img.save(tmp.name, "JPEG", quality=95)
            tmp_path = Path(tmp.name)

        cl = await asyncio.to_thread(_get_client)
        media = await asyncio.to_thread(cl.photo_upload, tmp_path, content["caption"])

        await db.mark_post_result(post["id"], "posted", external_post_id=str(media.pk))
        logger.info("posted promo for package %s to instagram (unofficial)", package["name"])
    except Exception as e:
        logger.exception("failed to post promo to instagram")
        await db.mark_post_result(post["id"], "failed", error_message=str(e))
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


async def run_forever():
    if not config.INSTAGRAM_UNOFFICIAL_ENABLED:
        logger.info("instagram unofficial module disabled (INSTAGRAM_UNOFFICIAL_ENABLED=false)")
        return
    if not _has_credentials():
        logger.warning("instagram unofficial credentials missing, module will not start")
        return

    while True:
        try:
            cl = await asyncio.to_thread(_get_client)
            await _handle_direct_messages(cl)
            await asyncio.sleep(random.uniform(20, 60))
            await _handle_comments(cl)
        except Exception:
            logger.exception("instagram unofficial poll cycle failed")
        await asyncio.sleep(random.uniform(MIN_POLL_INTERVAL_SECONDS, MAX_POLL_INTERVAL_SECONDS))
