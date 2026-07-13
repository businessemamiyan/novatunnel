from aiogram import Router, F
from aiogram.types import CallbackQuery

from shared import db, purchase_service

router = Router()


async def _is_purchase_owner_agent(callback: CallbackQuery, purchase_id: str):
    """تایید/رد پرداخت مشتریِ متصل به لینک اختصاصی فقط برای همان نماینده مجاز است — نه هر کاربری."""
    purchase = await db.get_purchase(purchase_id)
    if purchase is None:
        return None, None
    agent_user = await db.get_user_by_telegram_id(callback.from_user.id)
    if agent_user is None or purchase["seller_agent_id"] != agent_user["id"]:
        return purchase, False
    return purchase, True


@router.callback_query(F.data.startswith("agent_approve:"))
async def agent_approve_purchase(callback: CallbackQuery):
    purchase_id = callback.data.split(":", 1)[1]
    purchase, authorized = await _is_purchase_owner_agent(callback, purchase_id)
    if purchase is None:
        await callback.answer("این پرداخت پیدا نشد.", show_alert=True)
        return
    if not authorized:
        await callback.answer("این عملیات برای شما مجاز نیست.", show_alert=True)
        return

    result = await purchase_service.approve_purchase(purchase_id, callback.from_user.id)
    if result is None:
        await callback.answer("این پرداخت قبلاً پردازش شده است.", show_alert=True)
        return

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ تایید شد.\n{result['panel_status']}"
    )
    await callback.answer("تایید شد.")


@router.callback_query(F.data.startswith("agent_reject:"))
async def agent_reject_purchase(callback: CallbackQuery):
    purchase_id = callback.data.split(":", 1)[1]
    purchase, authorized = await _is_purchase_owner_agent(callback, purchase_id)
    if purchase is None:
        await callback.answer("این پرداخت پیدا نشد.", show_alert=True)
        return
    if not authorized:
        await callback.answer("این عملیات برای شما مجاز نیست.", show_alert=True)
        return

    result = await purchase_service.reject_purchase_service(purchase_id, callback.from_user.id)
    if result is None:
        await callback.answer("این پرداخت قبلاً پردازش شده است.", show_alert=True)
        return

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
    await callback.answer("رد شد.")
