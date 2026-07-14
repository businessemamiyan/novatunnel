import { useState } from "react";
import { useNavigate } from "react-router-dom";

type Tab = "referral" | "gift" | "credit" | "agency" | "packages" | "connection";

const TABS: { key: Tab; label: string }[] = [
  { key: "referral", label: "دعوت دوستان" },
  { key: "gift", label: "حجم هدیه" },
  { key: "credit", label: "اعتبار پاداش" },
  { key: "agency", label: "نمایندگی" },
  { key: "packages", label: "بسته‌ها" },
  { key: "connection", label: "🛡 اتصال پایدار" },
];

export default function Guide() {
  const [tab, setTab] = useState<Tab>("referral");
  const navigate = useNavigate();

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-1">📖 راهنمای کامل NovaTunnel</p>
      <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
        همه قوانین و مکانیزم‌های اپ، یک‌جا.
      </p>

      <div className="flex gap-2 mb-4 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="text-xs px-3 py-2 rounded-full"
            style={{
              background: tab === t.key ? "rgba(62,232,195,0.15)" : "var(--surface)",
              color: tab === t.key ? "var(--accent)" : "var(--text-secondary)",
              border: `1px solid ${tab === t.key ? "var(--accent)" : "var(--surface-border)"}`,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="glass-card p-4 text-sm leading-7" style={{ color: "var(--text-secondary)" }}>
        {tab === "referral" && (
          <div className="flex flex-col gap-3">
            <p className="font-medium m-0" style={{ color: "var(--text-primary)" }}>
              🎁 سیستم دعوت چندسطحی
            </p>
            <p>
              با معرفی دوستانت، از خرید اونا حجم رایگان می‌گیری — نه فقط از دوست مستقیمت، بلکه تا ۳ سطح پایین‌تر
              هم شامل می‌شه:
            </p>
            <p>🥇 سطح ۱ (دوست مستقیم): ۵٪ از حجم خریدش — حداکثر ۴ نفر، سقف ماهانه ۳۰ گیگ</p>
            <p>🥈 سطح ۲ (دوستِ دوستت): ۳٪ از حجم خریدش — حداکثر ۱۶ نفر، سقف ماهانه ۳۰ گیگ</p>
            <p>🥉 سطح ۳ (دوستِ دوستِ دوستت): ۱٪ از حجم خریدش — حداکثر ۶۴ نفر، سقف ماهانه ۴۰ گیگ</p>
            <p>سقف مطلق ماهانه (مجموع هر ۳ سطح): ۱۰۰ گیگ. مازاد بر سقف، حذف می‌شود و به ماه بعد منتقل نمی‌شود.</p>
            <p>
              ⚠️ برای دریافت هرگونه پاداش، باید شماره موبایلت رو توی ربات احراز کرده باشی — بدون احراز، پاداشی
              محاسبه نمی‌شود.
            </p>
          </div>
        )}

        {tab === "gift" && (
          <div className="flex flex-col gap-3">
            <p className="font-medium m-0" style={{ color: "var(--text-primary)" }}>
              🎁 فعال‌سازی و مصرف حجم هدیه
            </p>
            <p>حجم هدیه‌ای که از معرفی دوستان می‌گیری، ابتدا به‌صورت یک عدد انباشته در حسابت ذخیره می‌شود.</p>
            <p>
              برای مصرف این حجم، باید بسته «پنل کلید» (۵ گیگ / ۲۰,۰۰۰ تومان) را بخری — این خرید قفل مصرف حجم هدیه
              را باز می‌کند.
            </p>
            <p>
              ⏳ قانون ۴۰ روز: اگر ظرف ۴۰ روز از آخرین خریدت، خرید جدیدی ثبت نشود، کل حجم هدیه انباشته‌شده صفر
              می‌شود (بدون انتقال به بعد).
            </p>
            <p>🎉 هدیه خوش‌آمدگویی: با ثبت‌نام، مبلغی به کیف‌پولت اضافه می‌شود که در اولین خریدت به‌عنوان تخفیف نقدی کسر می‌شود.</p>
          </div>
        )}

        {tab === "credit" && (
          <div className="flex flex-col gap-3">
            <p className="font-medium m-0" style={{ color: "var(--text-primary)" }}>
              💳 اعتبار پاداش
            </p>
            <p>
              وقتی «پنل کلید» رو می‌خری، تمام حجم هدیه‌ای که تا اون لحظه جمع کردی، به نرخ ثابت ۵,۰۰۰ تومان به‌ازای
              هر گیگ، تبدیل می‌شود به یک موجودی جداگانه به اسم «اعتبار پاداش».
            </p>
            <p>این اعتبار فقط برای خرید بسته‌های حجم قابل استفاده است — قابل برداشت یا انتقال به دیگران نیست.</p>
            <p>موجودی اعتبار پاداشت رو می‌تونی توی صفحه «کیف پول» ببینی؛ در خریدهای بعدی خودکار کسر می‌شود.</p>
          </div>
        )}

        {tab === "agency" && (
          <div className="flex flex-col gap-3">
            <p className="font-medium m-0" style={{ color: "var(--text-primary)" }}>
              🏷 سیستم نمایندگی
            </p>
            <p>۳ رده نمایندگی وجود دارد که هرکدام هزینه فعال‌سازی و نرخ خرید هر گیگ مخصوص به خود را دارند:</p>
            <p>🥈 نقره‌ای — 🥇 طلایی — 💎 برلیان</p>
            <p>هر نماینده فقط یک نماینده دیگر معرفی می‌کند (زنجیره تک‌شاخه‌ای)، با عمق نامحدود.</p>
            <p>نماینده از کل زیرمجموعه زنجیره‌اش (مستقیم و غیرمستقیم) ۱٪ حجم هدیه می‌گیرد — سقف ۳۰۰ گیگ/۵۰ روز.</p>
            <p>حجمی که نماینده به‌عنوان پاداش می‌گیرد، برخلاف مشتری عادی، قابل فروش است.</p>
          </div>
        )}

        {tab === "packages" && (
          <div className="flex flex-col gap-3">
            <p className="font-medium m-0" style={{ color: "var(--text-primary)" }}>
              📦 بسته‌ها و قیمت‌ها
            </p>
            <p>۵ گیگ (پنل کلید) — ۲۰,۰۰۰ تومان</p>
            <p>۳۰ گیگ — ۲۰۰,۰۰۰ تومان</p>
            <p>۵۰ گیگ — ۲۵۰,۰۰۰ تومان</p>
            <p>۱۰۰ گیگ — ۴۰۰,۰۰۰ تومان</p>
            <p>پرداخت: کارت‌به‌کارت (با تایید ادمین) یا پرداخت آنلاین.</p>
          </div>
        )}

        {tab === "connection" && (
          <div className="flex flex-col gap-3">
            <p className="font-medium m-0" style={{ color: "var(--text-primary)" }}>
              🛡 اتصال پایدار (برای وقتی فیلترینگ سنگین شد)
            </p>
            <p>
              لینک اشتراک شما همیشه شامل ۲ پروفایل سرور است، نه فقط یکی — برنامه شما (v2rayNG، Streisand، Hiddify و
              مشابه) هر دو را زیر یک لینک نشون می‌ده:
            </p>
            <p>۱️⃣ <b>پروفایل اصلی:</b> سریع‌ترین حالت، برای استفاده روزمره.</p>
            <p>۲️⃣ <b>پروفایل پشتیبان (CDN):</b> ترافیکش شبیه یک بازدید عادی از یک سایت معروف دیده می‌شه — اگه
              پروفایل اصلی در فیلترینگ سنگین کار نکرد، همین یکی رو توی برنامه‌تون انتخاب کنید.</p>
            <p>
              ⚠️ نکته مهم: هیچ سرویسی (نه فقط ما) نمی‌تونه تضمین کنه در یک قطعی کامل و صددرصدی اینترنت بین‌الملل
              کار کنه — این محدودیت در سطح زیرساخت کشوره، نه چیزی که با نرم‌افزار حل بشه. آنچه بالا گفتیم برای
              فیلترینگ سنگین و قطعی‌های موضعی/انتخابی طراحی شده که سناریوی رایج‌تره.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
