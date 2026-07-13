import httpx

from shared import config

REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
STARTPAY_URL = "https://www.zarinpal.com/pg/StartPay/{authority}"


class ZarinpalError(Exception):
    pass


def is_configured() -> bool:
    return bool(config.ZARINPAL_MERCHANT_ID)


async def request_payment(amount_toman: int, description: str, callback_path: str) -> str:
    """پرداخت جدید در زرین‌پال ثبت می‌کند و authority را برمی‌گرداند."""
    if not is_configured():
        raise ZarinpalError("درگاه زرین‌پال تنظیم نشده است")

    callback_url = f"{config.APP_BASE_URL.rstrip('/')}{callback_path}"
    async with httpx.AsyncClient(timeout=20, proxy=config.ZARINPAL_SOCKS_PROXY or None) as client:
        resp = await client.post(REQUEST_URL, json={
            "merchant_id": config.ZARINPAL_MERCHANT_ID,
            "amount": amount_toman,
            "currency": "IRT",
            "callback_url": callback_url,
            "description": description,
        })
        data = resp.json()

    result = data.get("data") or {}
    if result.get("code") != 100:
        errors = data.get("errors") or result
        raise ZarinpalError(f"خطا در ایجاد پرداخت زرین‌پال: {errors}")

    return result["authority"]


def payment_url(authority: str) -> str:
    return STARTPAY_URL.format(authority=authority)


async def verify_payment(amount_toman: int, authority: str) -> str:
    """پرداخت را تایید می‌کند و ref_id را برمی‌گرداند. کد ۱۰۰ یا ۱۰۱ هر دو موفق است."""
    if not is_configured():
        raise ZarinpalError("درگاه زرین‌پال تنظیم نشده است")

    async with httpx.AsyncClient(timeout=20, proxy=config.ZARINPAL_SOCKS_PROXY or None) as client:
        resp = await client.post(VERIFY_URL, json={
            "merchant_id": config.ZARINPAL_MERCHANT_ID,
            "amount": amount_toman,
            "authority": authority,
            "currency": "IRT",
        })
        data = resp.json()

    result = data.get("data") or {}
    if result.get("code") not in (100, 101):
        errors = data.get("errors") or result
        raise ZarinpalError(f"پرداخت تایید نشد: {errors}")

    return str(result.get("ref_id", ""))
