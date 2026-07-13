from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from shared import db, marzban, qr, service_card
import keyboards
from handlers.purchase import show_packages

router = Router()


async def _send_services_list(target: Message):
    user = await db.get_user_by_telegram_id(target.chat.id)
    panels = await db.get_panels_for_user(user["id"])
    if not panels:
        await target.answer("شما هنوز هیچ سرویسی ندارید. از منوی «🛒 خرید بسته» شروع کنید.")
        return

    panels_with_status = []
    for panel in panels:
        marzban_user = await marzban.get_marzban_user(panel["marzban_username"])
        status = service_card.compute_status(panel, marzban_user)
        panels_with_status.append((panel, status))

    await target.answer("سرویس‌های شما:", reply_markup=keyboards.services_list_kb(panels_with_status))


@router.message(F.text == "🧩 مدیریت سرویس‌ها")
async def list_services(message: Message):
    await _send_services_list(message)


@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery):
    await callback.message.delete()
    await _send_services_list(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("svc:"))
async def show_service_detail(callback: CallbackQuery):
    panel_id = callback.data.split(":", 1)[1]
    panel = await db.get_panel(panel_id)
    if panel is None:
        await callback.answer("این سرویس پیدا نشد.", show_alert=True)
        return

    marzban_user = await marzban.get_marzban_user(panel["marzban_username"])
    sub_url = marzban.subscription_url(marzban_user) if marzban_user else "در دسترس نیست"
    card_text = service_card.format_service_card(panel, marzban_user, sub_url)

    if marzban_user:
        qr_buf = qr.generate_branded_qr(sub_url)
        await callback.message.answer_photo(
            BufferedInputFile(qr_buf.read(), filename="novatunnel_qr.png"),
            caption=card_text,
            reply_markup=keyboards.service_detail_kb(panel_id),
        )
    else:
        await callback.message.answer(card_text, reply_markup=keyboards.service_detail_kb(panel_id))
    await callback.answer()


@router.callback_query(F.data.startswith("renew:"))
async def renew_service(callback: CallbackQuery, state: FSMContext):
    panel_id = callback.data.split(":", 1)[1]
    await state.clear()
    await show_packages(callback.message, callback.from_user.id, state, renewed_panel_id=panel_id)
    await callback.answer()


@router.callback_query(F.data.startswith("delsvc_confirm:"))
async def do_delete(callback: CallbackQuery):
    panel_id = callback.data.split(":", 1)[1]
    panel = await db.get_panel(panel_id)
    if panel:
        try:
            await marzban.delete_service(panel["marzban_username"])
        except Exception:
            pass
        await db.deactivate_panel(panel_id)
    await callback.message.edit_caption(caption="🗑 این سرویس حذف شد.")
    await callback.answer("حذف شد.")


@router.callback_query(F.data.startswith("delsvc:"))
async def confirm_delete(callback: CallbackQuery):
    panel_id = callback.data.split(":", 1)[1]
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n⚠️ آیا از حذف این سرویس مطمئن هستید؟",
        reply_markup=keyboards.confirm_delete_kb(panel_id),
    )
    await callback.answer()
