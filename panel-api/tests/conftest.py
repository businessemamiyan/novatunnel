import os
import sys

# باید قبل از import هر ماژولی که config.py (خودِ panel-api یا shared) را import می‌کند تنظیم شود،
# چون هر دو در سطح ماژول os.environ[...] اجباری می‌خوانند.
os.environ.setdefault("BOT_TOKEN", "test-bot-token-123")
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
os.environ.setdefault("MARZBAN_ADMIN_USER", "unused")
os.environ.setdefault("MARZBAN_ADMIN_PASSWORD", "unused")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
