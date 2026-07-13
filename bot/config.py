import os
from dotenv import load_dotenv

load_dotenv()

from shared.config import *  # noqa: F401,F403

ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])

REQUIRED_INSTAGRAM_URL = os.environ.get(
    "REQUIRED_INSTAGRAM_URL", "https://www.instagram.com/novatunnel"
)

MINIAPP_URL = os.environ.get("MINIAPP_URL", "https://app.novaprd.ir/")
