import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from shared import db
from filters import IsAdmin
from states import SupportStates

router = Router()

USER_ID_RE = re.compile(r"id=(\d+)")


@router.message(F.text == "🎫 پشتیبانی")
async def start_support(message: Message, state: FSMContext):
    await state.set_state(SupportStates.waiting_message)
    await message.answer("پیام خود را بنویسید، به‌زودی پاسخ داده می‌شود:")


@router.message(SupportStates.waiting_message)
async def relay_to_admin(message: Message, state: FSMContext):
    text = (
        f"🎫 پیام پشتیبانی از {message.from_user.full_name} "
        f"(@{message.from_user.username}) id={message.from_user.id}:\n\n{message.text}"
    )
    for admin_id in await db.get_all_active_admin_ids():
        await message.bot.send_message(admin_id, text)
    await message.answer("پیام شما برای پشتیبانی ارسال شد.")
    await state.clear()


@router.message(IsAdmin(), F.reply_to_message)
async def relay_admin_reply(message: Message):
    original = message.reply_to_message.text or message.reply_to_message.caption or ""
    match = USER_ID_RE.search(original)
    if not match:
        return
    user_telegram_id = int(match.group(1))
    await message.bot.send_message(
        user_telegram_id,
        f"🎫 پاسخ پشتیبانی:\n\n{message.text}",
    )
    await message.answer("پاسخ برای کاربر ارسال شد.")
