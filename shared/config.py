import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

MARZBAN_BASE_URL = os.environ.get("MARZBAN_BASE_URL", "https://panel.novaprd.ir:8000")
MARZBAN_ADMIN_USER = os.environ["MARZBAN_ADMIN_USER"]
MARZBAN_ADMIN_PASSWORD = os.environ["MARZBAN_ADMIN_PASSWORD"]

SERVER_LOCATION = os.environ.get("SERVER_LOCATION", "🇳🇱 هلند (آمستردام)")
SERVICE_VALIDITY_DAYS = int(os.environ.get("SERVICE_VALIDITY_DAYS", "30"))

# لایه اتوماسیون تبلیغات/فروش — بدون این تنظیمات، تولید محتوا و پاسخ هوشمند غیرفعال می‌مانند
# (نه خطا می‌دهند، فقط پیام‌ها بدون پاسخ AI به ادمین ارجاع داده می‌شوند).
# Gemini/OpenAI/Claude از ایران مسدودند؛ به‌جای آن‌ها از Cloudflare Workers AI (رایگان، همون اکانت Cloudflare فعلی) استفاده می‌کنیم.
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_AI_TOKEN = os.environ.get("CLOUDFLARE_AI_TOKEN", "")
CLOUDFLARE_AI_MODEL = os.environ.get("CLOUDFLARE_AI_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")

REQUIRED_CHANNEL = os.environ.get("REQUIRED_CHANNEL", "novatunnelch")

CARD_NUMBER = os.environ.get("CARD_NUMBER", "0000-0000-0000-0000")
CARD_HOLDER = os.environ.get("CARD_HOLDER", "NovaTunnel")

# هدیه خوش‌آمدگویی فوری کیف‌پول برای ثبت‌نام اول (تومان) — صفر یعنی غیرفعال
WELCOME_GIFT_TOMAN = int(os.environ.get("WELCOME_GIFT_TOMAN", "10000"))

# نرخ تبدیل حجم هدیه انباشته به «اعتبار پاداش» (تومان به‌ازای هر گیگ) — با خرید پنل کلید فعال می‌شود
GIFT_GB_TO_REWARD_CREDIT_TOMAN = int(os.environ.get("GIFT_GB_TO_REWARD_CREDIT_TOMAN", "5000"))

# ساعت ارسال پیام روزانه انگیزشی صبحگاهی (وقت تهران)
DAILY_MOTIVATION_HOUR = int(os.environ.get("DAILY_MOTIVATION_HOUR", "8"))

# گروه داخلی تیم برای اعلان خطاهای پرداخت/باگ‌های سیستم — اختیاری، خالی یعنی این هشدارها فقط در لاگ سرور می‌مانند
TEAM_ALERT_GROUP_CHAT_ID = os.environ.get("TEAM_ALERT_GROUP_CHAT_ID", "")

# درگاه پرداخت آنی زرین‌پال — خالی یعنی گزینه پرداخت آنلاین غیرفعال می‌ماند (فقط کارت‌به‌کارت)
ZARINPAL_MERCHANT_ID = os.environ.get("ZARINPAL_MERCHANT_ID", "")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://app.novaprd.ir")

# زرین‌پال از IP خارج ایران در دسترس نیست؛ ترافیک این درخواست‌ها از یک تونل SSH به سرور داخل ایران رد می‌شود
ZARINPAL_SOCKS_PROXY = os.environ.get("ZARINPAL_SOCKS_PROXY", "")
