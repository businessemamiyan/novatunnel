from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
)

import config


def join_check_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="عضویت در کانال تلگرام",
                              url=f"https://t.me/{config.REQUIRED_CHANNEL}")],
        [InlineKeyboardButton(text="فالو اینستاگرام",
                              url=config.REQUIRED_INSTAGRAM_URL)],
        [InlineKeyboardButton(text="✅ عضو شدم، بررسی کن", callback_data="check_join")],
    ])


def main_menu_kb():
    rows = [
        [KeyboardButton(text="🚀 اپلیکیشن NovaTunnel", web_app=WebAppInfo(url=config.MINIAPP_URL))],
        [KeyboardButton(text="🛒 خرید بسته"), KeyboardButton(text="🧩 مدیریت سرویس‌ها")],
        [KeyboardButton(text="👛 کیف پول"), KeyboardButton(text="🎁 حجم هدیه من")],
        [KeyboardButton(text="👥 دعوت از دوستان"), KeyboardButton(text="🎫 پشتیبانی")],
    ]
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=rows)


def request_phone_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[KeyboardButton(text="📱 ارسال شماره موبایل من", request_contact=True)]],
    )


def guide_button_row():
    return [InlineKeyboardButton(text="📖 راهنمای اتصال", callback_data="guide")]


def packages_kb(packages):
    rows = []
    for p in packages:
        badge = f" ({p['badge']})" if p.get("badge") else ""
        label = f"{p['name']}{badge} — {int(p['retail_price_toman']):,} تومان"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pkg:{p['id']}")])
    rows.append([InlineKeyboardButton(text="🎟 دارم کد تخفیف دارم", callback_data="have_discount")])
    rows.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_purchase")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_price_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تایید و پرداخت", callback_data="confirm_price")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_purchase")],
    ])


def cancel_only_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 انصراف", callback_data="cancel_purchase")],
    ])


def services_list_kb(panels_with_status):
    rows = [
        [InlineKeyboardButton(text=f"{status} {panel['label'] or panel['marzban_username']}",
                              callback_data=f"svc:{panel['id']}")]
        for panel, status in panels_with_status
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_detail_kb(panel_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔁 تمدید سریع", callback_data=f"renew:{panel_id}"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"delsvc:{panel_id}"),
        ],
        guide_button_row(),
        [InlineKeyboardButton(text="🔙 لیست سرویس‌ها", callback_data="back_to_services")],
    ])


def confirm_delete_kb(panel_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله، حذف کن", callback_data=f"delsvc_confirm:{panel_id}"),
            InlineKeyboardButton(text="❌ انصراف", callback_data=f"svc:{panel_id}"),
        ],
    ])


def admin_purchase_kb(purchase_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تایید پرداخت", callback_data=f"approve:{purchase_id}"),
            InlineKeyboardButton(text="❌ رد کردن", callback_data=f"reject:{purchase_id}"),
        ]
    ])
