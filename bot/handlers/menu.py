import logging
from urllib.parse import quote

from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from shared import db
import keyboards

router = Router()
logger = logging.getLogger(__name__)

GUIDE_TEXT = (
    "┏━━━━━━━━━━━━━━━━━━━┓\n"
    "     📖 <b>راهنمای اتصال</b>\n"
    "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
    "۱. یکی از اپ‌های زیر را نصب کنید:\n"
    "   • اندروید: v2rayNG یا Happ\n"
    "   • iOS: Streisand یا Happ\n"
    "   • ویندوز/مک: NekoBox یا Hiddify Next\n\n"
    "۲. لینک اشتراک (Subscription) بالا را کپی کنید.\n"
    "۳. در اپ، گزینه Import from Clipboard / Add Subscription را بزنید.\n"
    "۴. یا به‌سادگی QR کد را با همان اپ اسکن کنید.\n"
    "۵. روی Connect بزنید و لذت ببرید 🚀"
)


@router.callback_query(F.data == "guide")
async def show_guide(callback: CallbackQuery):
    await callback.message.answer(GUIDE_TEXT)
    await callback.answer()


@router.message(F.text == "🎁 حجم هدیه من")
async def my_gift_volume(message: Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("لطفاً ابتدا دستور /start را بزنید.")
        return

    phone_status = "احراز شده ✅" if user["phone_verified"] else "احراز نشده ⚠️"
    text = (
        f"🎁 حجم هدیه انباشته شما: {float(user['gift_balance_gb']):.2f} گیگابایت\n"
        f"📱 وضعیت احراز موبایل: {phone_status}\n\n"
        f"برای مصرف حجم هدیه، باید بسته «پنل کلید» (۵ گیگ) خریداری کرده باشید.\n"
        f"اگر ظرف ۴۰ روز از آخرین خرید، خرید جدیدی ثبت نشود، حجم هدیه انباشته سوخته می‌شود."
    )
    if not user["phone_verified"]:
        text += "\n\n⚠️ بدون احراز شماره موبایل، هیچ پاداشی از معرفی دوستان دریافت نمی‌کنید."
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 احراز شماره موبایل", callback_data="start_phone_verify")]
        ]))
    else:
        await message.answer(text)


@router.callback_query(F.data == "start_phone_verify")
async def start_phone_verify(callback: CallbackQuery):
    logger.info("start_phone_verify triggered by telegram_id=%s", callback.from_user.id)
    await callback.message.answer(
        "برای احراز، دکمه زیر رو بزن تا شماره موبایلت (همون شماره تلگرامت) رو برام بفرستی:",
        reply_markup=keyboards.request_phone_kb(),
    )
    await callback.answer()


@router.message(F.contact)
async def receive_phone_contact(message: Message):
    contact = message.contact
    logger.info(
        "receive_phone_contact triggered: from_user=%s contact_user_id=%s phone=%s",
        message.from_user.id, contact.user_id, contact.phone_number,
    )
    try:
        if contact.user_id is not None and contact.user_id != message.from_user.id:
            await message.answer(
                "لطفاً فقط شماره موبایل خودتان را ارسال کنید.", reply_markup=keyboards.main_menu_kb()
            )
            return

        await db.verify_phone(message.from_user.id, contact.phone_number)
        await message.answer(
            "✅ شماره موبایل شما با موفقیت احراز شد. از این به بعد پاداش معرفی دوستان برایتان محاسبه می‌شود.",
            reply_markup=keyboards.main_menu_kb(),
        )
    except Exception:
        logger.exception("receive_phone_contact failed for telegram_id=%s", message.from_user.id)
        await message.answer(
            "⚠️ مشکلی در ثبت احراز پیش اومد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
            reply_markup=keyboards.main_menu_kb(),
        )


@router.message(F.text == "👥 دعوت از دوستان")
async def invite_friends(message: Message):
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    share_text = "اینترنت پرسرعت و پایدار + با دعوت از دوستات حجم رایگان بگیر 🎁"
    share_url = f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(share_text)}"

    await message.answer(
        "🎁 <b>لینک اختصاصی خودتو داری!</b>\n\n"
        "با هر خریدی که دوستات (تا ۳ سطح پایین‌تر) با این لینک بزنن، حجم رایگان می‌گیری —\n"
        "هرچی شبکه‌ت بزرگ‌تر، حجم بیشتر و هزینه‌ت به سمت صفر می‌ره 🚀\n\n"
        f"<code>{link}</code>\n\n"
        "👇 دکمه زیر رو بزن و مستقیم برای دوستات یا گروه‌هات بفرست (سریع‌تر از کپی‌پیست!)\n\n"
        "⚠️ برای دریافت پاداش، باید شماره موبایلتو احراز کرده باشی.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 اشتراک‌گذاری با دوستان", url=share_url)],
        ]),
    )
