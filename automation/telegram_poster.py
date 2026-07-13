import logging
import random

import httpx

import config
from shared import ai_client, content_generator, db, promo_image

logger = logging.getLogger(__name__)

BOT_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"


async def get_bot_username() -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{BOT_API}/getMe")
        r.raise_for_status()
        return r.json()["result"]["username"]


async def _send_photo(channel: str, image_bytes: bytes, caption: str):
    chat_id = channel if channel.startswith("@") or channel.startswith("-") else f"@{channel}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BOT_API}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption},
            files={"photo": ("promo.png", image_bytes, "image/png")},
        )
        r.raise_for_status()
        result = r.json()
        if not result.get("ok"):
            raise RuntimeError(result)
        return result["result"]["message_id"]


async def _pick_topic_and_package():
    """موضوع پست بعدی را طوری انتخاب می‌کند که موضوع (و در حالت معرفی بسته، خود بسته) اخیراً تکرار نشده باشد."""
    recent = await db.get_recent_post_topics("telegram", limit=5)
    recent_categories = {t.split(":", 1)[0] for t in recent}

    pool = [t for t in content_generator.TOPICS if t not in recent_categories]
    if not pool:
        pool = content_generator.TOPICS
    topic = random.choice(pool)

    if topic != "package_promo":
        return topic, None, topic

    packages = await db.get_active_packages()
    if not packages:
        return None, None, None

    recent_package_ids = {t.split(":", 1)[1] for t in recent if t.startswith("package_promo:")}
    candidates = [p for p in packages if str(p["id"]) not in recent_package_ids] or packages
    package = random.choice(candidates)
    return topic, package, f"package_promo:{package['id']}"


async def post_scheduled_content():
    topic, package, topic_tag = await _pick_topic_and_package()
    if topic is None:
        logger.info("no active packages, skipping scheduled post")
        return

    try:
        bot_username = await get_bot_username()
        content = await content_generator.generate_topic_post_content(topic, bot_username, package=package)
    except ai_client.AINotConfigured:
        logger.warning("AI provider not configured, skipping content generation")
        return
    except Exception:
        logger.exception("failed to generate post content")
        return

    post = await db.create_generated_post("telegram", content["caption"], topic=topic_tag)

    try:
        image_buf = promo_image.generate_promo_image(
            content["headline"], content["price_line"], content["subtitle"], content["cta"]
        )
        message_id = await _send_photo(config.REQUIRED_CHANNEL, image_buf.getvalue(), content["caption"])
        await db.mark_post_result(post["id"], "posted", external_post_id=str(message_id))
        logger.info("posted topic=%s to telegram channel", topic_tag)
    except Exception as e:
        logger.exception("failed to post to telegram")
        await db.mark_post_result(post["id"], "failed", error_message=str(e))
