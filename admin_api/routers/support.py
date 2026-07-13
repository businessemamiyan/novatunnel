from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from shared import notify
from auth import get_current_user

router = APIRouter()


TOPIC_LABELS = {
    "payment": "💳 مشکل پرداخت",
    "connection": "🌐 مشکل اتصال",
    "general": "❓ سوال عمومی",
    "agency": "🤝 درخواست نمایندگی",
}


class SupportMessage(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    topic: str | None = None


@router.post("")
async def send_support_message(body: SupportMessage, user: dict = Depends(get_current_user)):
    topic_label = TOPIC_LABELS.get(body.topic or "", "🎫 سایر")
    text = (
        f"{topic_label} — پیام پشتیبانی از Mini App\n"
        f"{user.get('first_name') or ''} (@{user.get('username')}) id={user['telegram_id']}:\n\n{body.message}"
    )
    await notify.notify_admins(text)
    return {"ok": True}
