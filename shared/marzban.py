import time
import uuid

import httpx

from . import config

_token = None
_token_expiry = 0.0


async def _get_token() -> str:
    global _token, _token_expiry
    if _token and time.time() < _token_expiry:
        return _token
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{config.MARZBAN_BASE_URL}/api/admin/token",
            data={"username": config.MARZBAN_ADMIN_USER, "password": config.MARZBAN_ADMIN_PASSWORD},
        )
        r.raise_for_status()
        _token = r.json()["access_token"]
        _token_expiry = time.time() + 3000
    return _token


async def get_marzban_user(username: str):
    token = await _get_token()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{config.MARZBAN_BASE_URL}/api/user/{username}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def create_new_service(telegram_id: int, volume_gb: float, expire_at: int, is_vip: bool = False):
    """هر خرید = یک سرویس مستقل: یک اکانت Marzban کاملاً جدید با یوزرنیم یکتا می‌سازد.
    is_vip=True فقط برای خریداران بسته ویژه — اینباند اختصاصی رله سرور ایران (شرایط سخت) را هم اضافه می‌کند."""
    username = f"nt_{telegram_id}_{uuid.uuid4().hex[:8]}"
    data_bytes = int(volume_gb * 1024 ** 3)
    token = await _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    inbounds = ["VLESS TCP REALITY", "VLESS WS TLS CDN"]
    if is_vip:
        inbounds.append("VLESS TCP REALITY VIP")
    body = {
        "username": username,
        "proxies": {"vless": {"id": str(uuid.uuid4()), "flow": "xtls-rprx-vision"}},
        "inbounds": {"vless": inbounds},
        "expire": expire_at,
        "data_limit": data_bytes,
        "data_limit_reset_strategy": "no_reset",
        "status": "active",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{config.MARZBAN_BASE_URL}/api/user", headers=headers, json=body)
        r.raise_for_status()
        return username, r.json()


async def renew_service(username: str, add_volume_gb: float, new_expire_at: int):
    """تمدید سرویس موجود: حجم اضافه می‌شود (روی حجم مصرف‌نشده قبلی) و تاریخ انقضا تمدید می‌شود."""
    existing = await get_marzban_user(username)
    add_bytes = int(add_volume_gb * 1024 ** 3)
    current_limit = (existing["data_limit"] or 0) if existing else 0
    token = await _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    body = {
        "data_limit": current_limit + add_bytes,
        "expire": new_expire_at,
        "status": "active",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.put(f"{config.MARZBAN_BASE_URL}/api/user/{username}", headers=headers, json=body)
        r.raise_for_status()
        return r.json()


async def set_service_status(username: str, status: str):
    """status: 'active' یا 'disabled'"""
    token = await _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.put(
            f"{config.MARZBAN_BASE_URL}/api/user/{username}", headers=headers, json={"status": status}
        )
        r.raise_for_status()
        return r.json()


async def revoke_subscription(username: str):
    """لینک اشتراک قبلی را باطل و لینک جدید صادر می‌کند (مثلاً اگر لینک قبلی به اشتراک گذاشته شده باشد)."""
    token = await _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{config.MARZBAN_BASE_URL}/api/user/{username}/revoke_sub", headers=headers)
        r.raise_for_status()
        return r.json()


async def delete_service(username: str):
    token = await _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.delete(f"{config.MARZBAN_BASE_URL}/api/user/{username}", headers=headers)
        if r.status_code not in (200, 204, 404):
            r.raise_for_status()


async def get_all_users():
    """همه‌ی کاربران Marzban را صفحه‌به‌صفحه می‌گیرد — برای sync دوره‌ای حجم مصرفی."""
    token = await _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    all_users = []
    offset = 0
    limit = 200
    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            r = await client.get(
                f"{config.MARZBAN_BASE_URL}/api/users",
                headers=headers,
                params={"offset": offset, "limit": limit},
            )
            r.raise_for_status()
            data = r.json()
            users = data.get("users", [])
            all_users.extend(users)
            total = data.get("total", len(all_users))
            offset += limit
            if offset >= total or not users:
                break
    return all_users


def subscription_url(marzban_user: dict) -> str:
    return f"{config.MARZBAN_BASE_URL}{marzban_user['subscription_url']}"
