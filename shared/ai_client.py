import json

import httpx

from . import config


class AINotConfigured(Exception):
    pass


async def ask_ai(system_prompt: str, user_message: str, max_tokens: int = 1024,
                  history: list[dict] | None = None, temperature: float = 0.4) -> str:
    if not config.CLOUDFLARE_ACCOUNT_ID or not config.CLOUDFLARE_AI_TOKEN:
        raise AINotConfigured("CLOUDFLARE_ACCOUNT_ID یا CLOUDFLARE_AI_TOKEN تنظیم نشده است.")

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{config.CLOUDFLARE_ACCOUNT_ID}/ai/run/{config.CLOUDFLARE_AI_MODEL}"
    )
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {config.CLOUDFLARE_AI_TOKEN}"}

    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    if not data.get("success"):
        raise RuntimeError(f"خطای Cloudflare Workers AI: {data.get('errors')}")

    result = data.get("result") or {}
    choices = result.get("choices")
    if choices:
        # "response" را Cloudflare وقتی خروجی مدل شبیه JSON باشد خودکار به dict تبدیل می‌کند؛
        # choices[0].message.content همیشه رشته خام است، پس منبع قابل‌اعتمادتریه.
        text = choices[0]["message"]["content"]
    else:
        text = result.get("response")
        if isinstance(text, dict):
            text = json.dumps(text, ensure_ascii=False)

    if not isinstance(text, str):
        raise RuntimeError(f"پاسخ غیرمنتظره از Cloudflare Workers AI: {data}")
    return text.strip()
