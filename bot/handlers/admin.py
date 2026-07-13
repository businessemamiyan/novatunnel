from aiogram import Router, F
from aiogram.types import CallbackQuery

from shared import db, purchase_service
from filters import IsAdmin

router = Router()
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data.startswith("approve:"))
async def approve_purchase(callback: CallbackQuery):
    purchase_id = callback.data.split(":", 1)[1]
    result = await purchase_service.approve_purchase(purchase_id, callback.from_user.id)
    if result is None:
        await callback.answer("این پرداخت قبلاً پردازش شده است.", show_alert=True)
        return

    reward_summary = "\n".join(
        f"  سطح {level}: +{amount:.2f} گیگ به کاربر {ancestor_id}"
        for ancestor_id, level, amount in result["rewards"]
    ) or "  (بدون پاداش قابل پرداخت)"

    admin_name = callback.from_user.full_name
    await callback.message.edit_caption(
        caption=callback.message.caption
        + f"\n\n✅ تایید شد توسط {admin_name}.\n{result['panel_status']}\nپاداش‌های اعمال‌شده:\n{reward_summary}"
    )
    await callback.answer("تایید شد.")


@router.callback_query(F.data.startswith("reject:"))
async def reject_purchase(callback: CallbackQuery):
    purchase_id = callback.data.split(":", 1)[1]
    purchase = await purchase_service.reject_purchase_service(purchase_id, callback.from_user.id)
    if purchase is None:
        await callback.answer("این پرداخت قبلاً پردازش شده است.", show_alert=True)
        return

    admin_name = callback.from_user.full_name
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n❌ رد شد توسط {admin_name}.")
    await callback.answer("رد شد.")


@router.callback_query(F.data.startswith("wtopup_approve:"))
async def approve_wallet_topup(callback: CallbackQuery):
    topup_id = callback.data.split(":", 1)[1]
    topup = await db.confirm_wallet_topup(topup_id)
    if topup is None:
        await callback.answer("این درخواست قبلاً پردازش شده است.", show_alert=True)
        return

    buyer = await db.get_user_by_id(topup["user_id"])
    await callback.bot.send_message(
        buyer["telegram_id"],
        f"✅ شارژ کیف‌پول شما به مبلغ {int(topup['amount_toman']):,} تومان تایید شد.",
    )
    admin_name = callback.from_user.full_name
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ تایید شد توسط {admin_name}.")
    await callback.answer("تایید شد.")


@router.callback_query(F.data.startswith("wtopup_reject:"))
async def reject_wallet_topup(callback: CallbackQuery):
    topup_id = callback.data.split(":", 1)[1]
    topup = await db.reject_wallet_topup(topup_id)
    if topup is None:
        await callback.answer("این درخواست قبلاً پردازش شده است.", show_alert=True)
        return

    buyer = await db.get_user_by_id(topup["user_id"])
    await callback.bot.send_message(buyer["telegram_id"], "❌ درخواست شارژ کیف‌پول شما تایید نشد.")
    admin_name = callback.from_user.full_name
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n❌ رد شد توسط {admin_name}.")
    await callback.answer("رد شد.")


@router.callback_query(F.data.startswith("agency_approve:"))
async def approve_agency_activation(callback: CallbackQuery):
    request_id = callback.data.split(":", 1)[1]
    agent = await db.confirm_agency_activation_request(request_id)
    if agent is None:
        await callback.answer("این درخواست قبلاً پردازش شده است.", show_alert=True)
        return

    buyer = await db.get_user_by_id(agent["user_id"])
    await callback.bot.send_message(
        buyer["telegram_id"], f"🎉 پنل نمایندگی رده «{agent['tier']}» شما فعال شد!",
    )
    admin_name = callback.from_user.full_name
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ تایید شد توسط {admin_name}.")
    await callback.answer("تایید شد.")


@router.callback_query(F.data.startswith("agency_reject:"))
async def reject_agency_activation(callback: CallbackQuery):
    request_id = callback.data.split(":", 1)[1]
    req = await db.reject_agency_activation_request(request_id)
    if req is None:
        await callback.answer("این درخواست قبلاً پردازش شده است.", show_alert=True)
        return

    buyer = await db.get_user_by_id(req["user_id"])
    await callback.bot.send_message(buyer["telegram_id"], "❌ درخواست فعال‌سازی نمایندگی شما تایید نشد.")
    admin_name = callback.from_user.full_name
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n❌ رد شد توسط {admin_name}.")
    await callback.answer("رد شد.")
