import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db, marzban, purchase_service
from auth import get_current_admin

router = APIRouter()


class RenewBody(BaseModel):
    add_volume_gb: float
    extend_days: int = 30


class GrantBody(BaseModel):
    telegram_id: int
    volume_gb: float
    service_label: str | None = None
    is_vip_service: bool = False


@router.get("")
async def list_services(status: str | None = None, search: str | None = None,
                         limit: int = 50, offset: int = 0,
                         admin: dict = Depends(get_current_admin)):
    panels = await db.get_all_panels(status, search, limit, offset)
    return [dict(p) for p in panels]


@router.delete("/{panel_id}")
async def delete_service(panel_id: str, admin: dict = Depends(get_current_admin)):
    panel = await db.get_panel(panel_id)
    if panel is None:
        raise HTTPException(404, "not found")
    try:
        await marzban.delete_service(panel["marzban_username"])
    except Exception:
        pass
    await db.deactivate_panel(panel_id)
    await db.log_admin_action(admin["telegram_id"], "service_delete", panel["marzban_username"])
    return {"ok": True}


@router.post("/grant")
async def grant_test_service(body: GrantBody, admin: dict = Depends(get_current_admin)):
    """اعطای دستی سرویس تست/رایگان — در حسابداری/آمار فروش لحاظ نمی‌شود (purchases.is_test)."""
    buyer = await db.get_user_by_telegram_id(body.telegram_id)
    if buyer is None:
        raise HTTPException(404, "این کاربر هنوز در ربات ثبت‌نام نکرده است")
    if body.volume_gb <= 0:
        raise HTTPException(400, "حجم باید بزرگتر از صفر باشد")

    purchase = await db.create_test_grant_purchase(
        buyer["id"], body.volume_gb, body.service_label, body.is_vip_service
    )
    try:
        panel_status = await purchase_service.deliver_service_for_purchase(purchase, buyer)
    except Exception as e:
        panel_status = f"⚠️ خطا در ساخت/تمدید پنل Marzban: {e}"

    await db.log_admin_action(
        admin["telegram_id"], "service_test_grant", f"user {body.telegram_id}",
        {"volume_gb": body.volume_gb, "is_vip_service": body.is_vip_service},
    )
    return {"id": str(purchase["id"]), "panel_status": panel_status}


@router.post("/{panel_id}/renew")
async def renew_service(panel_id: str, body: RenewBody, admin: dict = Depends(get_current_admin)):
    panel = await db.get_panel(panel_id)
    if panel is None:
        raise HTTPException(404, "not found")

    now = datetime.datetime.now(datetime.timezone.utc)
    base = panel["expires_at"] if panel["expires_at"] and panel["expires_at"] > now else now
    new_expires_at = base + datetime.timedelta(days=body.extend_days)

    await marzban.renew_service(panel["marzban_username"], body.add_volume_gb, int(new_expires_at.timestamp()))
    await db.renew_panel(panel_id, body.add_volume_gb, new_expires_at)
    await db.log_admin_action(
        admin["telegram_id"], "service_renew", panel["marzban_username"],
        {"add_volume_gb": body.add_volume_gb, "extend_days": body.extend_days},
    )
    return {"ok": True}
