from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class CardCreate(BaseModel):
    card_number: str
    card_holder: str


class CardUpdate(BaseModel):
    card_number: str
    card_holder: str
    is_active: bool


@router.get("")
async def list_cards(admin: dict = Depends(get_current_admin)):
    rows = await db.get_all_payment_cards()
    return [dict(r) for r in rows]


@router.post("")
async def create_card(body: CardCreate, admin: dict = Depends(get_current_admin)):
    card = await db.create_payment_card(body.card_number, body.card_holder)
    await db.log_admin_action(admin["telegram_id"], "payment_card_create", None, {"card_number": body.card_number})
    return dict(card)


@router.patch("/{card_id}")
async def update_card(card_id: int, body: CardUpdate, admin: dict = Depends(get_current_admin)):
    card = await db.update_payment_card(card_id, body.card_number, body.card_holder, body.is_active)
    if card is None:
        raise HTTPException(404, "not found")
    await db.log_admin_action(admin["telegram_id"], "payment_card_update", f"card {card_id}", {})
    return dict(card)


@router.delete("/{card_id}")
async def delete_card(card_id: int, admin: dict = Depends(get_current_admin)):
    await db.delete_payment_card(card_id)
    await db.log_admin_action(admin["telegram_id"], "payment_card_delete", f"card {card_id}")
    return {"ok": True}
