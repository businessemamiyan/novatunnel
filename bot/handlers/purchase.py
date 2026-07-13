from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from shared import db, purchase_service
import keyboards
from states import PurchaseStates

router = Router()


async def show_packages(target, telegram_id: int, state: FSMContext, renewed_panel_id=None):
    await state.set_state(PurchaseStates.choosing_package)
    if renewed_panel_id:
        await state.update_data(renewed_panel_id=str(renewed_panel_id))

    user = await db.get_user_by_telegram_id(telegram_id)
    if user:
        packages = await db.get_purchasable_packages(user["id"], user["gift_balance_gb"])
    else:
        packages = await db.get_active_packages()

    await target.answer("یکی از بسته‌ها را انتخاب کنید:", reply_markup=keyboards.packages_kb(packages))


@router.message(F.text == "🛒 خرید بسته")
async def start_purchase(message: Message, state: FSMContext):
    await state.clear()
    await show_packages(message, message.from_user.id, state)


@router.callback_query(F.data == "cancel_purchase")
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("purchase_id"):
        await db.reject_purchase(data["purchase_id"])
    await state.clear()
    await callback.message.delete()
    await callback.answer("لغو شد.")


@router.callback_query(F.data == "have_discount", PurchaseStates.choosing_package)
async def ask_discount_code(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PurchaseStates.entering_discount_code)
    await callback.message.answer("کد تخفیف خود را وارد کنید:", reply_markup=keyboards.cancel_only_kb())
    await callback.answer()


@router.message(PurchaseStates.entering_discount_code)
async def receive_discount_code(message: Message, state: FSMContext):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    discount = await db.find_discount_code(message.text)

    if discount is None:
        await message.answer("کد تخفیف نامعتبر است. دوباره تلاش کنید یا /start را بزنید.")
        return

    if discount["expires_at"] and discount["expires_at"].timestamp() < message.date.timestamp():
        await message.answer("این کد تخفیف منقضی شده است.")
        return

    if discount["max_uses"] is not None and discount["used_count"] >= discount["max_uses"]:
        await message.answer("ظرفیت استفاده از این کد تخفیف تمام شده است.")
        return

    if await db.user_used_discount_code(discount["id"], user["id"]):
        await message.answer("شما قبلاً از این کد تخفیف استفاده کرده‌اید.")
        return

    await state.update_data(discount_code_id=str(discount["id"]),
                             discount_type=discount["discount_type"],
                             discount_value=float(discount["discount_value"]),
                             min_purchase_toman=int(discount["min_purchase_toman"]))
    await state.set_state(PurchaseStates.choosing_package)
    packages = await db.get_purchasable_packages(user["id"], user["gift_balance_gb"])
    await message.answer("کد تخفیف اعمال شد ✅ حالا بسته موردنظر را انتخاب کنید:",
                          reply_markup=keyboards.packages_kb(packages))


@router.callback_query(F.data.startswith("pkg:"), PurchaseStates.choosing_package)
async def choose_package(callback: CallbackQuery, state: FSMContext):
    package_id = int(callback.data.split(":", 1)[1])
    package = await db.get_package(package_id)
    if package is None:
        await callback.answer("این بسته دیگر موجود نیست.", show_alert=True)
        return

    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if package["is_key_panel"]:
        if not await db.can_purchase_key_panel(user["id"], user["gift_balance_gb"]):
            await callback.answer(
                "پنل کلید فقط برای کاربرانی است که حجم هدیه دارند ولی سرویس فعالی ندارند.",
                show_alert=True,
            )
            return

    agent_pricing = await db.get_agent_pricing_for_customer(user["id"])
    price = int(agent_pricing.get(package_id, package["retail_price_toman"]))
    data = await state.get_data()
    discount_amount = 0
    discount_code_id = data.get("discount_code_id")

    if discount_code_id:
        if price < data.get("min_purchase_toman", 0):
            await callback.answer("مبلغ این بسته کمتر از حداقل خرید مجاز برای این کد تخفیف است.", show_alert=True)
            return
        discount_row = {"discount_type": data["discount_type"], "discount_value": data["discount_value"]}
        discount_amount = db.compute_discount_amount(discount_row, price)

    final_price = price - discount_amount

    reward_credit_used = 0
    if final_price > 0:
        reward_credit_balance = float(user["reward_credit_toman"])
        if reward_credit_balance > 0:
            reward_credit_used = min(reward_credit_balance, final_price)
            final_price -= reward_credit_used

    wallet_used = 0
    if final_price > 0:
        wallet_balance = int(user["wallet_balance_toman"])
        if wallet_balance > 0:
            wallet_used = min(wallet_balance, final_price)
            final_price -= wallet_used

    await state.update_data(package_id=package_id, price=price, discount_amount=discount_amount,
                             wallet_used=wallet_used, reward_credit_used=reward_credit_used,
                             final_price=final_price)

    if data.get("renewed_panel_id"):
        # تمدید: اسم سرویس همان قبلی می‌ماند، مستقیم برو سراغ تایید قیمت
        await show_price_confirmation(callback.message, state, edit=True)
    else:
        await state.set_state(PurchaseStates.entering_service_name)
        await callback.message.edit_text(
            "یک اسم دلخواه برای این سرویس انتخاب کنید (مثلاً «گوشی من» یا «لپ‌تاپ»):"
        )
    await callback.answer()


@router.message(PurchaseStates.entering_service_name)
async def receive_service_name(message: Message, state: FSMContext):
    label = message.text.strip()[:64]
    if not label:
        await message.answer("لطفاً یک اسم معتبر وارد کنید.")
        return
    await state.update_data(service_label=label)
    await show_price_confirmation(message, state, edit=False)


async def show_price_confirmation(target, state: FSMContext, edit: bool):
    data = await state.get_data()
    package = await db.get_package(data["package_id"])
    label = data.get("service_label", "تمدید سرویس")

    text = f"🔖 سرویس: {label}\n📦 بسته: {package['name']}\n💰 قیمت: {data['price']:,} تومان\n"
    if data.get("discount_amount"):
        text += f"🎟 تخفیف: {data['discount_amount']:,} تومان\n"
    if data.get("reward_credit_used"):
        text += f"🎁 استفاده از اعتبار پاداش: {data['reward_credit_used']:,} تومان\n"
    if data.get("wallet_used"):
        text += f"👛 استفاده از کیف‌پول: {data['wallet_used']:,} تومان\n"
    if data.get("discount_amount") or data.get("wallet_used") or data.get("reward_credit_used"):
        text += f"💵 مبلغ نهایی: {data['final_price']:,} تومان\n"
    text += "\nبرای ادامه تایید کنید:"

    await state.set_state(PurchaseStates.confirming_price)
    if edit:
        await target.edit_text(text, reply_markup=keyboards.confirm_price_kb())
    else:
        await target.answer(text, reply_markup=keyboards.confirm_price_kb())


@router.callback_query(F.data == "confirm_price", PurchaseStates.confirming_price)
async def confirm_price(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    package = await db.get_package(data["package_id"])

    binding = await db.get_customer_agent_binding(user["id"])
    purchase = await db.create_pending_purchase(
        user["id"], package["id"], package["volume_gb"], data["final_price"],
        discount_code_id=data.get("discount_code_id"),
        discount_amount_toman=data.get("discount_amount", 0),
        service_label=data.get("service_label"),
        renewed_panel_id=data.get("renewed_panel_id"),
        wallet_credit_used_toman=data.get("wallet_used", 0),
        reward_credit_used_toman=data.get("reward_credit_used", 0),
        seller_agent_id=binding["agent_id"] if binding else None,
    )

    if data["final_price"] <= 0:
        # کل مبلغ از کیف‌پول/اعتبار پاداش پوشش داده شد — نیازی به رسید کارت‌به‌کارت نیست، مستقیم تحویل بده
        await state.clear()
        await callback.message.edit_text("💵 کل مبلغ پرداخت شد. سرویس شما در حال آماده‌سازی است...")
        await purchase_service.approve_purchase(purchase["id"], callback.from_user.id)
        await callback.answer()
        return

    await state.update_data(purchase_id=str(purchase["id"]))
    await state.set_state(PurchaseStates.waiting_receipt)

    card_number, card_holder = await purchase_service.get_payment_card()
    await callback.message.edit_text(
        f"لطفاً مبلغ {data['final_price']:,} تومان را به شماره کارت زیر واریز کنید:\n\n"
        f"💳 {card_number}\nبه نام: {card_holder}\n\n"
        f"{purchase_service.PAYMENT_SAFETY_NOTICE}\n\n"
        "سپس عکس رسید پرداخت را همین‌جا ارسال کنید.",
        reply_markup=keyboards.cancel_only_kb(),
    )
    await callback.answer()


@router.message(PurchaseStates.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    purchase = await db.get_purchase(data["purchase_id"])
    user = await db.get_user_by_telegram_id(message.from_user.id)
    package = await db.get_package(purchase["package_id"])

    await db.update_purchase_receipt_file_id(purchase["id"], message.photo[-1].file_id)

    label = purchase["service_label"] or "(تمدید سرویس موجود)"
    caption = (
        f"🧾 رسید پرداخت جدید\n"
        f"کاربر: {user['full_name']} (@{message.from_user.username}) id={message.from_user.id}\n"
        f"سرویس: {label}\n"
        f"بسته: {package['name']}\n"
        f"مبلغ: {int(purchase['price_toman']):,} تومان\n"
        f"شناسه خرید: {purchase['id']}"
    )
    for admin_id in await db.get_all_active_admin_ids():
        await message.bot.send_photo(
            chat_id=admin_id,
            photo=message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboards.admin_purchase_kb(purchase["id"]),
        )
    await message.answer("پرداخت شما ثبت شد و در حال بررسی توسط ادمین است. نتیجه به همین چت اطلاع داده می‌شود.")
    await state.clear()


@router.message(PurchaseStates.waiting_receipt)
async def receipt_reminder(message: Message):
    await message.answer("لطفاً عکس رسید پرداخت را ارسال کنید.")
