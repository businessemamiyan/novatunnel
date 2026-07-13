import logging
import os
import random
import uuid

import httpx

import config
from shared import ai_client, content_generator, db, promo_image
from telegram_poster import get_bot_username

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
PROMO_STATIC_DIR = "/opt/novatunnel-admin-api/static/promo"
PROMO_PUBLIC_BASE = "https://app.novaprd.ir/promo"


class InstagramNotConfigured(Exception):
    pass


def _require_config():
    if not config.INSTAGRAM_ENABLED:
        raise InstagramNotConfigured("اتوماسیون پست اینستاگرام غیرفعال است (INSTAGRAM_ENABLED=false).")
    if not config.INSTAGRAM_ACCESS_TOKEN or not config.INSTAGRAM_BUSINESS_ACCOUNT_ID:
        raise InstagramNotConfigured("INSTAGRAM_ACCESS_TOKEN یا INSTAGRAM_BUSINESS_ACCOUNT_ID تنظیم نشده است.")


def _save_public_image(image_bytes: bytes) -> str:
    os.makedirs(PROMO_STATIC_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    with open(os.path.join(PROMO_STATIC_DIR, filename), "wb") as f:
        f.write(image_bytes)
    return f"{PROMO_PUBLIC_BASE}/{filename}"


async def _publish(image_url: str, caption: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        create_resp = await client.post(
            f"{GRAPH_API_BASE}/{config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": config.INSTAGRAM_ACCESS_TOKEN,
            },
        )
        create_resp.raise_for_status()
        creation_id = create_resp.json()["id"]

        publish_resp = await client.post(
            f"{GRAPH_API_BASE}/{config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish",
            data={"creation_id": creation_id, "access_token": config.INSTAGRAM_ACCESS_TOKEN},
        )
        publish_resp.raise_for_status()
        return publish_resp.json()["id"]


async def post_random_package_promo():
    try:
        _require_config()
    except InstagramNotConfigured as e:
        logger.info(str(e))
        return

    packages = await db.get_active_packages()
    if not packages:
        return
    package = random.choice(packages)

    try:
        bot_username = await get_bot_username()
        content = await content_generator.generate_post_content(package, bot_username, "instagram")
    except ai_client.AINotConfigured:
        logger.warning("GEMINI_API_KEY not set, skipping instagram content generation")
        return
    except Exception:
        logger.exception("failed to generate instagram post content")
        return

    post = await db.create_generated_post("instagram", content["caption"])

    try:
        image_buf = promo_image.generate_promo_image(
            content["headline"], content["price_line"], content["subtitle"], content.get("cta")
        )
        image_url = _save_public_image(image_buf.getvalue())
        media_id = await _publish(image_url, content["caption"])
        await db.mark_post_result(post["id"], "posted", external_post_id=media_id)
        logger.info("posted promo for package %s to instagram", package["name"])
    except Exception as e:
        logger.exception("failed to post promo to instagram")
        await db.mark_post_result(post["id"], "failed", error_message=str(e))
