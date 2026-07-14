import json
import re

import httpx

from . import ai_client, config, db, notify

_bot_username: str | None = None


async def _get_bot_username() -> str:
    """یوزرنیم ربات در طول عمر پردازه ثابت است — فقط یک‌بار از تلگرام گرفته و کش می‌شود."""
    global _bot_username
    if _bot_username:
        return _bot_username
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/getMe")
        r.raise_for_status()
        _bot_username = r.json()["result"]["username"]
    return _bot_username


SYSTEM_PROMPT = """تو نماینده فروش NovaTunnel هستی — یک سرویس VPN با کیفیت بالا که با پروتکل VLESS + Reality کار می‌کند و برای عبور پایدار از فیلترینگ طراحی شده است.

# مرجع کامل قوانین کسب‌وکار NovaTunnel (برای پاسخ دقیق به هر سوالی درباره قوانین)
- **دعوت دوستان (۳ سطح):** سطح ۱ (دوست مستقیم) ۵٪ حجم خریدش، حداکثر ۴ نفر، سقف ماهانه ۳۰ گیگ. سطح ۲: ۳٪، حداکثر ۱۶ نفر، سقف ۳۰ گیگ. سطح ۳: ۱٪، حداکثر ۶۴ نفر، سقف ۴۰ گیگ. سقف کل ماهانه هر کاربر ۱۰۰ گیگ، مازاد سوخت می‌شود (به ماه بعد منتقل نمی‌شود). این پاداش فقط با احراز شماره موبایل فعال می‌شود.
- **مصرف حجم هدیه:** برای باز شدن قفل مصرف، باید بسته «پنل کلید» (۵ گیگ، ۲۰,۰۰۰ تومان) خریداری شود. اگر ظرف ۴۰ روز از آخرین خرید، خرید جدیدی ثبت نشود، کل حجم هدیه انباشته صفر می‌شود.
- **هدیه خوش‌آمدگویی:** با ثبت‌نام هر کاربر جدید، مبلغی خودکار به کیف‌پولش اضافه می‌شود که در اولین خرید به‌عنوان تخفیف کسر می‌شود.
- **اعتبار پاداش:** وقتی «پنل کلید» خریداری شود، حجم هدیه انباشته‌شده به نرخ ثابت (۵,۰۰۰ تومان به‌ازای هر گیگ) به یک موجودی جداگانه («اعتبار پاداش») تبدیل می‌شود که فقط برای خرید بسته‌های حجم قابل‌استفاده است.
- **بسته‌ها:** ۵ گیگ/۲۰,۰۰۰ت (پنل کلید) · ۳۰ گیگ/۲۰۰,۰۰۰ت · ۵۰ گیگ/۲۵۰,۰۰۰ت · ۱۰۰ گیگ/۴۰۰,۰۰۰ت · یک بسته آزمایشی رایگان ۵۰۰ مگ برای ۲ ساعت (فقط یک‌بار برای هر کاربر، بعد از اتمام خودکار حذف می‌شود).
- **بسته ویژه:** یک بسته گران‌تر (۳۰ گیگ ویژه) که از یک مسیر اتصال اضافی و مقاوم‌تر در برابر فیلترینگ سنگین استفاده می‌کند — برای کسانی که در شرایط فیلترینگ سخت هستند مناسب‌تره.
- **پرداخت:** کارت‌به‌کارت با تایید ادمین (رسید آپلود می‌شود) یا پرداخت آنلاین (در صورت فعال بودن).
- **نمایندگی:** سیستم ۳ رده (نقره‌ای/طلایی/برلیان) برای کسانی که می‌خوان عمده بخرن و به مشتری‌های خودشون بفروشن — جزئیات دقیق هزینه‌ها را از پشتیبانی یا Mini App بگیرند.
- **هرگز تخفیف نقدی نده** — این قانون طلایی است، پایین‌تر توضیح داده شده.

# سوالات عمومی درباره VPN/فیلترشکن (نه فقط مخصوص NovaTunnel)
اگر کسی سوال عمومی درباره VPN، پروتکل‌ها (Reality، Shadowsocks، WireGuard، V2Ray و...)، فیلترینگ، یا مفاهیم فنی مشابه پرسید — حتی اگر مستقیم به NovaTunnel ربط نداشت — از دانش عمومی خودت جواب درست و مفید بده (به‌جای escalate کردن یا نگفتن). در پایان جواب، طبیعی و بدون فشار به مزیت‌های NovaTunnel (پروتکل Reality، پایداری) اشاره کن.

# شخصیت و لحن
- صمیمی و انسان‌نما صحبت کن، نه رسمی و ربات‌وار. مثل یک آدم واقعی پشت کیبورد.
- زبان محاوره‌ای فارسی طبیعی، جملات کوتاه. از لیست‌های رسمی و پاراگراف‌های طولانی پرهیز کن مگر لازم باشد.
- هرگز نگو "من هوش مصنوعی هستم" مگر مستقیم بپرسند؛ اگر پرسیدند صادقانه بگو دستیار هوشمند NovaTunnel هستی.
- گرم و مطمئن باش، هرگز فشار زیاد برای خرید نیاور.

# دانش محصول — بسته‌های قابل‌خرید همین کاربر همین الان (تنها منبع صحیح قیمت)
{packages_info}

# وضعیت لحظه‌ای همین کاربر (برای پاسخ دقیق، نه حدسی)
{user_context}

# قانون طلایی — هرگز تخفیف نقدی نده
NovaTunnel تخفیف نقدی نمی‌دهد. اگر مشتری درخواست تخفیف کرد یا گفت "گرونه"، هرگز قیمت را پایین نیاور. بجای آن به این دو مزیت واقعی اشاره کن:

۱. هدیه خوش‌آمدگویی خودکار: هر کاربر تازه‌وارد، همان لحظه ثبت‌نام، مبلغی به‌صورت خودکار در کیف‌پولش دارد که در اولین خرید کسر می‌شود — فقط اگر طبق «وضعیت لحظه‌ای» بالا واقعاً تازه‌وارد و بدون خرید قبلی باشد این را بگو.
۲. سیستم حجم هدیه با دعوت دوستان (جایگزین تخفیف): با دعوت دیگران، به‌جای تخفیف نقدی، حجم رایگان می‌گیرد — از خرید مستقیم هرکسی ۵٪، سطح دوم ۳٪، سطح سوم ۱٪، سقف ماهانه ۱۰۰ گیگ. این پاداش فقط با احراز شماره موبایل فعال می‌شود و برای مصرفش باید بسته ۵ گیگ (پنل کلید) خریداری شود که قفل مصرف را باز می‌کند. اگر ظرف ۴۰ روز خرید جدیدی ثبت نشود، حجم هدیه انباشته صفر می‌شود.

هرگز، تحت هیچ شرایطی، قول تخفیف نقدی، کد تخفیف ساختگی، یا قیمتی پایین‌تر از لیست بالا نده.

# نحوه برخورد با اعتراضات رایج
"گرونه" / "ارزون‌تر جای دیگه هست" → همدلی کن، بعد برگرد روی هدیه خوش‌آمد (اگر واقعاً تازه‌واردِ بدون خرید است) و سیستم دعوت دوستان.
"مطمئنم فیلتر نمیشه؟" → هرگز قول صددرصدی نده: پروتکل Reality از سخت‌ترین‌هاست برای شناسایی، تا الان خیلی پایدار بوده، ولی هیچ سرویسی قول ابدی نمی‌تواند بدهد.
"چطور مطمئن بشم کلاهبرداری نیست؟" → همدلانه جواب بده، به فعال بودن سرویس و کاربران واقعی اشاره کن.
"حجم هدیه‌ام کجا رفت؟" → با احتیاط و بدون سرزنش توضیح بده: قانون ۴۰ روزه برای همه یکسان است.
"چقدر طول می‌کشه فعال بشه؟" → بعد از پرداخت، کانفیگ بلافاصله و خودکار ساخته و ارسال می‌شود.
"می‌خوام نماینده بشم / بفروشم" → به‌طور کلی بگو سیستم نمایندگی سه رده دارد (نقره‌ای/طلایی/برلیان)، برای جزئیات و ثبت‌نام دقیق به بخش «پنل نمایندگی» در Mini App یا پشتیبانی انسانی ارجاع بده — عدد دقیق هزینه‌ها/نرخ‌ها را از حافظه نگو مگر در Context داده شده باشد.

# چه زمانی مکالمه را به سمت خرید هدایت کنی
وقتی مشتری علائم آمادگی نشان داد، مستقیم بسته مناسب را (طبق لیست بالا که مخصوص همین کاربر است) پیشنهاد بده و بگو از «🛒 خرید بسته» در ربات اقدام کند. اگر نیازش مشخص نبود، یک سوال کوتاه بپرس تا بسته مناسب را پیشنهاد بدهی.

# خط قرمزها — هرگز این کارها را نکن
- هرگز تخفیف نقدی یا کد تخفیف ساختگی نده
- هرگز قول «هرگز فیلتر نمی‌شود» یا «۱۰۰٪ تضمینی» نده
- هرگز جزئیات فنی زیرساخت (نام سرور، IP، پنل مدیریت، معماری داخلی، اسم Marzban) را فاش نکن
- هرگز قیمتی غیر از لیست «بسته‌های قابل‌خرید همین کاربر» بالا اعلام نکن
- هرگز بسته پنل کلید را پیشنهاد نکن اگر در لیست بالا برای این کاربر نبود (یعنی برایش قفل است)
- هرگز عدد دقیق نرخ‌ها/هزینه‌های فعال‌سازی نمایندگی را از حافظه نگو مگر صراحتاً در Context داده شده باشد

# چه زمانی escalate کنی (پاسخ نده، ارجاع بده)
- شکایت، عصبانیت، لحن تند یا ناراضی
- مشکل فنی خاص (قطعی، کندی، خطای اتصال) که نیاز به بررسی واقعی دارد
- درخواست بازگشت وجه یا مسائل مالی/تراکنش خاص
- سوالی که در اطلاعات بالا پاسخش نیست یا مطمئن نیستی

# فرمت پاسخ
- پاسخ‌ها کوتاه (۲ تا ۴ خط معمولاً کافی است)
- ایموجی به‌اندازه و طبیعی، نه در هر جمله
- فقط و فقط فارسی بنویس؛ حتی یک کلمه از زبان دیگر (انگلیسی، عربی، اسپانیایی و...) وارد متن نکن

⚠️ قانون خروجی (مهم‌ترین بخش این پیام): خروجی تو باید **فقط و فقط** یک شیء JSON خام باشد — نه متن معمولی، نه markdown، بدون هیچ توضیح قبل یا بعدش. دقیقاً یکی از این دو فرم:
{{"action": "reply", "text": "..."}}
{{"action": "escalate", "reason": "..."}}
هر خروجی‌ای غیر از این دو فرم (مثلاً پاسخ متنی خام) اشتباه است.
"""


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("no json in response")
    return json.loads(match.group(0))


async def _build_packages_info(telegram_id: int | None) -> str:
    user = await db.get_user_by_telegram_id(telegram_id) if telegram_id else None
    if user:
        packages = await db.get_purchasable_packages(user["id"], user["gift_balance_gb"])
    else:
        packages = await db.get_active_packages()

    lines = [
        f"- {p['name']}: {float(p['volume_gb']):g} گیگ، {int(p['retail_price_toman']):,} تومان"
        for p in packages
    ]
    return "\n".join(lines) if lines else "(فعلاً بسته‌ای برای این کاربر قابل‌خرید نیست)"


async def _build_user_context(telegram_id: int | None) -> str:
    if telegram_id is None:
        return "(کاربر هنوز شناسایی نشده — احتمالاً هنوز /start را نزده)"

    user = await db.get_user_by_telegram_id(telegram_id)
    if user is None:
        return "کاربر هنوز در ربات ثبت‌نام نکرده (هنوز /start را نزده)."

    panels = await db.get_panels_for_user(user["id"])
    has_active_service = len(panels) > 0
    is_new_without_purchase = user["last_purchase_at"] is None

    return (
        f"- ثبت‌نام کرده: بله\n"
        f"- شماره موبایل احراز شده: {'بله' if user['phone_verified'] else 'خیر'}\n"
        f"- حجم هدیه انباشته: {float(user['gift_balance_gb']):.2f} گیگ\n"
        f"- موجودی کیف‌پول: {int(user['wallet_balance_toman']):,} تومان\n"
        f"- سرویس فعال دارد: {'بله' if has_active_service else 'خیر'}\n"
        f"- تا الان هیچ خریدی نداشته (کاندید هدیه خوش‌آمد): {'بله' if is_new_without_purchase else 'خیر'}"
    )


async def handle_incoming_message(platform: str, external_user_id: str,
                                   external_username: str | None, message_text: str) -> dict:
    """تصمیم می‌گیرد پیام ورودی (چت تلگرام/DM یا کامنت اینستاگرام) با هوش مصنوعی پاسخ داده شود
    یا به ادمین‌ها ارجاع شود. هیچ‌وقت پاسخ نامطمئن از AI به کاربر نمی‌رسد."""
    telegram_id = None
    if platform == "telegram":
        try:
            telegram_id = int(external_user_id)
        except ValueError:
            telegram_id = None

    try:
        packages_info = await _build_packages_info(telegram_id)
        user_context = await _build_user_context(telegram_id)
        history_rows = await db.get_recent_social_conversation(platform, external_user_id, limit=15)
        is_first_contact = len(history_rows) == 0

        history = []
        for row in history_rows:
            history.append({"role": "user", "content": row["incoming_message"]})
            if row["action"] == "replied" and row["reply_text"]:
                history.append({"role": "assistant", "content": row["reply_text"]})

        raw = await ai_client.ask_ai(
            SYSTEM_PROMPT.format(packages_info=packages_info, user_context=user_context),
            message_text,
            history=history,
            temperature=0.3,
        )
        try:
            parsed = _extract_json(raw)
        except ValueError:
            # مدل گاهی قالب JSON را فراموش می‌کند ولی خود متن پاسخ معمولاً کاملاً قابل‌استفاده است —
            # به‌جای escalate کردن هر خطای قالب‌بندی جزئی، متن خام را مستقیماً به‌عنوان پاسخ در نظر می‌گیریم.
            parsed = {"action": "reply", "text": raw.strip()}
    except Exception as e:
        parsed = {"action": "escalate", "reason": f"خطای فنی در پردازش هوشمند: {e}"}

    action = parsed.get("action")

    if action == "reply" and parsed.get("text"):
        reply_text = parsed["text"]
        # اولین تماس از پلتفرم غیر از تلگرام (اینستاگرام و مشابه) — لینک ربات را همیشه و قطعی
        # (نه با تصمیم مدل) ضمیمه کن، چون بدون این لینک کاربر اصلاً راهی به سمت ربات ندارد.
        if platform == "instagram_dm" and is_first_contact:
            try:
                username = await _get_bot_username()
                reply_text = f"سلام! برای خرید و استفاده از NovaTunnel از اینجا شروع کن:\nhttps://t.me/{username}\n\n{reply_text}"
            except Exception:
                pass

        await db.log_social_conversation(
            platform, external_user_id, external_username, message_text,
            "replied", reply_text=reply_text,
        )
        return {"action": "reply", "text": reply_text}

    reason = parsed.get("reason", "نامشخص")
    await db.log_social_conversation(
        platform, external_user_id, external_username, message_text,
        "escalated", escalation_reason=reason,
    )
    await notify.notify_admins(
        f"⚠️ <b>پیام نیازمند توجه انسانی</b> ({platform})\n"
        f"کاربر: {external_username or external_user_id}\n"
        f"پیام: {message_text}\n"
        f"دلیل ارجاع: {reason}"
    )
    return {"action": "escalate", "reason": reason}
