import os
from dotenv import load_dotenv

load_dotenv()

from shared.config import *  # noqa: F401,F403

# ساعات پست خودکار روزانه (به وقت تهران)، جدا شده با کاما — مثلاً "10:00,18:00"
POST_TIMES = os.environ.get("POST_TIMES", "10:00,18:00")

INSTAGRAM_ENABLED = os.environ.get("INSTAGRAM_ENABLED", "false").lower() == "true"
INSTAGRAM_UNOFFICIAL_ENABLED = os.environ.get("INSTAGRAM_UNOFFICIAL_ENABLED", "false").lower() == "true"

# اینستاگرام رسمی (Graph API) — نیازمند اکانت بیزینسی + پیج فیسبوک متصل
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

# اینستاگرام غیررسمی (instagrapi) — حساب جداگانه، فقط برای پاسخ خودکار DM/کامنت
INSTAGRAM_UNOFFICIAL_USERNAME = os.environ.get("INSTAGRAM_UNOFFICIAL_USERNAME", "")
INSTAGRAM_UNOFFICIAL_PASSWORD = os.environ.get("INSTAGRAM_UNOFFICIAL_PASSWORD", "")
