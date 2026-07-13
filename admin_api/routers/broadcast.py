import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared import config, db
from auth import get_current_admin

router = APIRouter()


class BroadcastBody(BaseModel):
    text: str


@router.post("")
async def send_broadcast(body: BroadcastBody, admin: dict = Depends(get_current_admin)):
    user_ids = await db.get_all_user_telegram_ids()
    sent = 0
    failed = 0
    async with httpx.AsyncClient(timeout=15) as client:
        for uid in user_ids:
            try:
                r = await client.post(
                    f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
                    json={"chat_id": uid, "text": body.text, "parse_mode": "HTML"},
                )
                if r.status_code == 200:
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

    await db.log_admin_action(
        admin["telegram_id"], "broadcast_sent", None,
        {"recipients": len(user_ids), "sent": sent, "failed": failed},
    )
    return {"total": len(user_ids), "sent": sent, "failed": failed}
