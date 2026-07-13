from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery

import config
from shared import db
import keyboards

router = Router()


async def is_channel_member(bot, telegram_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{config.REQUIRED_CHANNEL}", user_id=telegram_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return False


WELCOME_TEMPLATE = (
    "درود بر تو {first_name} عزیز\n"
    "✨ به NovaTunnel خوش اومدی\n\n"
    "دروازه‌ی سریع و پایدار تو به دنیای آزاد اینترنت\n\n"
    "━━━━━━━━━━━━━━━\n"
    "⚡️ سرعت واقعی، بدون قطعی‌های اعصاب‌خردکن\n"
    "🛡️ امنیت و پایداری در اولویت\n"
    "🌍 دسترسی چندلوکیشنه به دنیای بی‌مرز\n"
    "━━━━━━━━━━━━━━━\n\n"
    "🎁 اقتصادی‌ترین راه؟ دعوت از دوستات!\n"
    "با معرفی هر دوست، حجم رایگان می‌گیری —\n"
    "هرچی شبکه‌ت بزرگ‌تر بشه، هزینه‌ت به سمت صفر می‌ره\n\n"
    "از منوی زیر شروع کن 👇"
)


async def send_main_menu(message: Message, first_name: str, is_new_user: bool = False):
    text = WELCOME_TEMPLATE.format(first_name=first_name or "کاربر")
    if is_new_user and config.WELCOME_GIFT_TOMAN > 0:
        text += f"\n\n🎉 هدیه خوش‌آمدگویی {config.WELCOME_GIFT_TOMAN:,} تومان به کیف‌پولت اضافه شد — همین حالا تو خرید اولت استفاده‌اش کن!"
    await message.answer(text, reply_markup=keyboards.main_menu_kb())


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    referrer_telegram_id = None
    agent_slug = None
    if command.args and command.args.startswith("ref_"):
        try:
            referrer_telegram_id = int(command.args.removeprefix("ref_"))
        except ValueError:
            referrer_telegram_id = None
    elif command.args and command.args.startswith("agent_"):
        agent_slug = command.args.removeprefix("agent_")

    user = await db.get_user_by_telegram_id(message.from_user.id)
    is_new_user = user is None
    if is_new_user:
        user = await db.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            referrer_telegram_id,
        )
        if config.WELCOME_GIFT_TOMAN > 0:
            await db.credit_wallet(
                user["id"], "initial_join_gift", config.WELCOME_GIFT_TOMAN,
                note="هدیه خوش‌آمدگویی ثبت‌نام",
            )
    else:
        await db.touch_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    if agent_slug:
        agent = await db.get_agent_by_slug(agent_slug)
        if agent:
            await db.bind_customer_to_agent(user["id"], agent["user_id"])

    if await is_channel_member(message.bot, message.from_user.id):
        await send_main_menu(message, message.from_user.first_name, is_new_user=is_new_user)
    else:
        await message.answer(
            "قبل از استفاده از ربات، لطفاً در کانال تلگرام و اینستاگرام ما عضو/فالو شوید:",
            reply_markup=keyboards.join_check_kb(),
        )


@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery):
    if await is_channel_member(callback.bot, callback.from_user.id):
        await callback.message.delete()
        await send_main_menu(callback.message, callback.from_user.first_name)
    else:
        await callback.answer("هنوز در کانال عضو نشده‌اید.", show_alert=True)
