import jdatetime
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from shared import db
from filters import IsAdmin

router = Router()


def _bar(value: float, max_value: float, width: int = 12) -> str:
    if max_value <= 0:
        return "▁" * width
    filled = max(0, min(width, round((value / max_value) * width)))
    return "█" * filled + "▁" * (width - filled)


async def _build_stats_text() -> str:
    accounts = await db.get_account_stats()
    volume = await db.get_volume_stats()
    sales = await db.get_sales_stats()
    trend = await db.get_daily_sales_trend(7)

    max_day = max((float(d["total"]) for d in trend), default=0)
    trend_lines = []
    for d in trend:
        jd = jdatetime.date.fromgregorian(date=d["day"])
        label = jd.strftime("%m/%d")
        trend_lines.append(f"{label}  {_bar(float(d['total']), max_day)}  {int(d['total']):,}")
    trend_text = "\n".join(trend_lines) if trend_lines else "داده‌ای برای نمایش نیست."

    return (
        "┏━━━━━━━━━━━━━━━━━━━┓\n"
        "   📊 داشبورد NovaTunnel\n"
        "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
        "👥 <b>اکانت‌ها</b>\n"
        f"  کل ساخته‌شده: {accounts['total']}\n"
        f"  🟢 فعال: {accounts['active']}\n"
        f"  🔴 منقضی/غیرفعال: {accounts['inactive']}\n\n"
        "📦 <b>حجم</b>\n"
        f"  تخصیص داده‌شده: {float(volume['total_allocated_gb']):.1f} گیگ\n"
        f"  مصرف‌شده: {float(volume['total_used_gb']):.1f} گیگ\n\n"
        "💰 <b>فروش (تومان)</b>\n"
        f"  امروز: {int(sales['today_sales']):,}\n"
        f"  ۷ روز اخیر: {int(sales['week_sales']):,}\n"
        f"  این ماه: {int(sales['month_sales']):,}\n"
        f"  کل: {int(sales['total_sales']):,}\n\n"
        "📈 <b>روند ۷ روز اخیر</b>\n"
        f"<code>{trend_text}</code>"
    )


async def _build_admins_text() -> str:
    admins = await db.list_admins()
    lines = [
        f"• {a['telegram_id']}" + ("  (بنیان‌گذار)" if a["added_by"] is None else "")
        for a in admins
    ]
    return "👤 <b>ادمین‌های فعال:</b>\n" + "\n".join(lines)


# پنل کامل مدیریت (سرویس‌ها، رسیدها، قیمت‌گذاری، Broadcast، لاگ) داخل Mini App است —
# دستورات زیر فقط یک میانبر سریع برای زمانی که Mini App در دسترس نیست باقی مانده‌اند.


@router.message(Command("stats"), IsAdmin())
async def show_stats(message: Message):
    await message.answer(await _build_stats_text())


@router.message(Command("addadmin"), IsAdmin())
async def add_admin_cmd(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().lstrip("-").isdigit():
        await message.answer("فرمت درست: /addadmin آیدی_عددی_تلگرام")
        return
    new_id = int(command.args.strip())
    await db.add_admin(new_id, message.from_user.id)
    await message.answer(f"✅ کاربر {new_id} به‌عنوان ادمین اضافه شد.")
    try:
        await message.bot.send_message(
            new_id, "🎉 شما به‌عنوان ادمین ربات NovaTunnel اضافه شدید.\nبرای مشاهده پنل مدیریت، /start را بزنید."
        )
    except Exception:
        pass


@router.message(Command("removeadmin"), IsAdmin())
async def remove_admin_cmd(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().lstrip("-").isdigit():
        await message.answer("فرمت درست: /removeadmin آیدی_عددی_تلگرام")
        return
    target_id = int(command.args.strip())
    if await db.count_active_admins() <= 1:
        await message.answer("⚠️ نمی‌توان آخرین ادمین فعال را حذف کرد.")
        return
    await db.remove_admin(target_id)
    await message.answer(f"🗑 دسترسی ادمین کاربر {target_id} حذف شد.")


@router.message(Command("listadmins"), IsAdmin())
async def list_admins_cmd(message: Message):
    await message.answer(await _build_admins_text())


@router.message(Command("adminhelp"), IsAdmin())
async def admin_help(message: Message):
    await message.answer(
        "🛠 <b>دستورات ادمین:</b>\n"
        "برای پنل کامل (سرویس‌ها، رسیدها، قیمت‌گذاری، Broadcast، لاگ):\n"
        "دکمه «🚀 اپلیکیشن NovaTunnel» در منوی اصلی.\n\n"
        "میانبرهای سریع:\n"
        "/stats — داشبورد آماری\n"
        "/addadmin آیدی — افزودن ادمین جدید\n"
        "/removeadmin آیدی — حذف دسترسی ادمین\n"
        "/listadmins — لیست ادمین‌های فعال"
    )
