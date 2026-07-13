import json
import re

from . import ai_client

TONE_GUIDE = """لحن: خیلی پرانرژی، شیطون، طنزآمیز و صمیمی — نه خشک و رسمی، نه شبیه تبلیغ شرکتی.
مثل یه دوست باحال که یه خبر هیجان‌انگیز داره، نه یه بنر تبلیغاتی.
از ایموجی‌های زیاد و مرتبط استفاده کن، جمله‌های کوتاه و ضربتی بنویس، از تعجب/سوال بازی‌گوشانه استفاده کن.
کلمات حساس (فیلترشکن/دور زدن تحریم/VPN مستقیم) را نگو، به‌جایش «اینترنت پرسرعت و پایدار» یا «دنیای آزاد اینترنت» بگو.
بدون وعده غیرواقعی."""

OUTPUT_SCHEMA = """فقط و فقط یک JSON خام (بدون markdown fence) با این فرم برگردان:
{
  "headline": "یک عبارت کوتاه و ضربتی برای روی تصویر (حداکثر ۴-۵ کلمه)",
  "price_line": "یک آمار/عدد کلیدی کوتاه برای روی تصویر (مثلاً قیمت، درصد، یا مقدار گیگ)",
  "subtitle": "یک جمله کوتاه زیر آن (حداکثر ۸ کلمه)",
  "cta": "متن کوتاه دکمه/فراخوان",
  "caption": "کپشن کامل پست برای انتشار (۴ تا ۶ جمله، پرانرژی و جذاب، + ۲-۳ هشتگ مرتبط در انتها)"
}"""

TOPIC_PROMPTS = {
    "package_promo": """تو کپی‌رایتر تبلیغاتی NovaTunnel هستی — پلتفرم فروش VPN (پروتکل VLESS+Reality) برای کاربران ایرانی.
{tone}

این پست باید یه بسته خاص رو با هیجان معرفی کنه:
- نام: {package_name}
- حجم: {volume_gb:g} گیگابایت
- قیمت: {price:,} تومان
- لینک سفارش: ربات تلگرام @{bot_username}

{schema}""",

    "gift_volume": """تو کپی‌رایتر NovaTunnel هستی. این پست باید سیستم «حجم هدیه از دعوت دوستان» رو با هیجان توضیح بده
(کاربر با دعوت دوستاش، تا ۳ سطح، از خرید اونا حجم رایگان می‌گیره — سطح ۱: ۵٪، سطح ۲: ۳٪، سطح ۳: ۱٪).
لینک شروع: ربات تلگرام @{bot_username}
{tone}

{schema}""",

    "referral_rules": """تو کپی‌رایتر NovaTunnel هستی. این پست باید یکی از این قوانین رو با یه لحن شیطون و هشدارگونه (نه خشک) یادآوری کنه
(هر بار فقط یکی رو انتخاب کن و روش تمرکز کن):
- بدون احراز شماره موبایل، هیچ پاداشی از دعوت دوستان محاسبه نمی‌شه
- اگه ظرف ۴۰ روز از آخرین خرید، خرید جدید ثبت نشه، کل حجم هدیه انباشته صفر می‌شه (می‌سوزه)
- برای مصرف حجم هدیه، باید «پنل کلید» (۵ گیگ، ۲۰,۰۰۰ تومان) رو بخری تا قفلش باز بشه
لینک: ربات تلگرام @{bot_username}
{tone}

{schema}""",

    "reward_credit": """تو کپی‌رایتر NovaTunnel هستی. این پست باید ویژگی «اعتبار پاداش» رو با هیجان معرفی کنه:
بعد از خرید پنل کلید، کل حجم هدیه انباشته به نرخ ۵,۰۰۰ تومان به‌ازای هر گیگ تبدیل میشه به یه اعتبار خرید قابل‌استفاده برای بسته‌های بعدی.
لینک: ربات تلگرام @{bot_username}
{tone}

{schema}""",

    "service_quality": """تو کپی‌رایتر NovaTunnel هستی. این پست باید روی کیفیت خود سرویس تمرکز کنه (نه قیمت یه بسته خاص):
سرعت بالا، پایداری، اتصال آسون با اسکن QR، بدون تنظیمات پیچیده، پشتیبانی سریع.
لینک: ربات تلگرام @{bot_username}
{tone}

{schema}""",
}

TOPICS = list(TOPIC_PROMPTS.keys())


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("no json in response")
    return json.loads(match.group(0))


async def generate_topic_post_content(topic: str, bot_username: str, package: dict | None = None) -> dict:
    """محتوای پست را بر اساس یک موضوع (نه صرفاً معرفی یک بسته) تولید می‌کند —
    برای تنوع محتوای اتوماسیون شبکه‌های اجتماعی (نه فقط تبلیغ بسته‌ها)."""
    template = TOPIC_PROMPTS[topic]
    prompt = template.format(
        tone=TONE_GUIDE,
        schema=OUTPUT_SCHEMA,
        bot_username=bot_username,
        package_name=package["name"] if package else "",
        volume_gb=float(package["volume_gb"]) if package else 0,
        price=int(package["retail_price_toman"]) if package else 0,
    )
    raw = await ai_client.ask_ai(prompt, "پست را بر اساس اطلاعات بالا بساز.")
    return _extract_json(raw)


async def generate_post_content(package: dict, bot_username: str, platform: str) -> dict:
    """سازگاری با کد قدیمی (پست Instagram هنوز از همین مسیر استفاده می‌کند)."""
    return await generate_topic_post_content("package_promo", bot_username, package=package)


MOTIVATION_SYSTEM_PROMPT = """تو یه دوست دلسوز و پرانرژی هستی که هر روز صبح یه پیام انگیزشی کوتاه فارسی برای کاربران NovaTunnel می‌فرستی.

قوانین مهم:
- این پیام تبلیغاتی نیست و نباید هیچ اشاره‌ای به بسته، قیمت، خرید یا NovaTunnel داشته باشد — فقط حال خوب و انرژی مثبت برای شروع روز.
- کوتاه (۲ تا ۳ جمله)، گرم، صمیمی، با یکی‌دو ایموجی مناسب.
- محتوا باید هر روز متفاوت و تازه باشد (یه جمله انگیزشی، یه نگاه مثبت به روز جدید، یا یه یادآوری کوچک برای مراقبت از خود).

فقط و فقط متن پیام را برگردان، بدون هیچ توضیح یا فرمت اضافه."""


async def generate_motivational_message() -> str:
    return await ai_client.ask_ai(MOTIVATION_SYSTEM_PROMPT, "پیام امروز را بساز.", max_tokens=200)
