from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from shared import smart_reply

router = Router()


@router.message(default_state, F.text, ~F.text.startswith("/"))
async def smart_reply_fallback(message: Message, state: FSMContext):
    result = await smart_reply.handle_incoming_message(
        platform="telegram",
        external_user_id=str(message.from_user.id),
        external_username=message.from_user.username,
        message_text=message.text,
    )
    if result["action"] == "reply":
        await message.answer(result["text"])
    else:
        await message.answer(
            "پیام شما دریافت شد و برای بررسی به پشتیبانی ارجاع داده شد. به‌زودی پاسخ داده می‌شود."
        )
