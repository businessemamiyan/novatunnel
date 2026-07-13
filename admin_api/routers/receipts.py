import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from shared import config, db, purchase_service
from auth import get_current_admin

router = APIRouter()


@router.get("")
async def list_receipts(status: str | None = None, limit: int = 50, offset: int = 0,
                         admin: dict = Depends(get_current_admin)):
    rows = await db.get_receipts(status, limit, offset)
    return [dict(r) for r in rows]


@router.post("/{purchase_id}/approve")
async def approve(purchase_id: str, admin: dict = Depends(get_current_admin)):
    result = await purchase_service.approve_purchase(purchase_id, admin["telegram_id"])
    if result is None:
        raise HTTPException(409, "already processed")
    return {"ok": True, "panel_status": result["panel_status"], "rewards": len(result["rewards"])}


@router.post("/{purchase_id}/reject")
async def reject(purchase_id: str, admin: dict = Depends(get_current_admin)):
    purchase = await purchase_service.reject_purchase_service(purchase_id, admin["telegram_id"])
    if purchase is None:
        raise HTTPException(409, "already processed")
    return {"ok": True}


@router.get("/{purchase_id}/photo")
async def get_photo(purchase_id: str, admin: dict = Depends(get_current_admin)):
    purchase = await db.get_purchase(purchase_id)
    if purchase is None or not purchase["receipt_file_id"]:
        raise HTTPException(404, "no receipt")

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile",
            params={"file_id": purchase["receipt_file_id"]},
        )
        r.raise_for_status()
        file_path = r.json()["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
        img_resp = await client.get(file_url)
        img_resp.raise_for_status()

    return StreamingResponse(iter([img_resp.content]), media_type="image/jpeg")
