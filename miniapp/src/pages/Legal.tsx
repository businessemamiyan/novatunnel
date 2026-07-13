import { useState } from "react";
import { useNavigate } from "react-router-dom";

type Tab = "terms" | "privacy";

export default function Legal() {
  const [tab, setTab] = useState<Tab>("terms");
  const navigate = useNavigate();

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">📄 قوانین و حریم خصوصی</p>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setTab("terms")}
          className="flex-1 text-sm px-3 py-2 rounded-full"
          style={{
            background: tab === "terms" ? "rgba(62,232,195,0.15)" : "transparent",
            color: tab === "terms" ? "var(--accent)" : "var(--text-secondary)",
          }}
        >
          قوانین استفاده
        </button>
        <button
          onClick={() => setTab("privacy")}
          className="flex-1 text-sm px-3 py-2 rounded-full"
          style={{
            background: tab === "privacy" ? "rgba(62,232,195,0.15)" : "transparent",
            color: tab === "privacy" ? "var(--accent)" : "var(--text-secondary)",
          }}
        >
          حریم خصوصی
        </button>
      </div>

      <div className="glass-card p-4 text-sm leading-7" style={{ color: "var(--text-secondary)" }}>
        {tab === "terms" ? (
          <div className="flex flex-col gap-3">
            <p>۱. با خرید هر بسته، اعتبار سرویس شما به مدت ۳۰ روز از لحظه فعال‌سازی معتبر است.</p>
            <p>۲. پرداخت کارت‌به‌کارت پس از ارسال رسید، توسط تیم پشتیبانی بررسی و در کوتاه‌ترین زمان ممکن تایید می‌شود.</p>
            <p>۳. حجم هدیه دریافتی از معرفی دوستان، قابل تبدیل به وجه نقد نیست و صرفاً برای مصرف در سرویس‌های NovaTunnel قابل استفاده است.</p>
            <p>۴. در صورت عدم خرید جدید ظرف ۴۰ روز از آخرین خرید، حجم هدیه انباشته‌شده صفر می‌شود.</p>
            <p>۵. مسئولیت استفاده از سرویس مطابق قوانین جاری کشور بر عهده کاربر است.</p>
            <p>۶. NovaTunnel هیچ تضمینی برای دسترسی ۱۰۰٪ بدون قطعی ارائه نمی‌دهد، اما تلاش می‌کند پایدارترین سرویس ممکن را فراهم کند.</p>
            <p>۷. برای هرگونه درخواست بازگشت وجه، از طریق بخش «تماس با پشتیبانی» اقدام کنید تا بررسی شود.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <p>۱. برای استفاده از این اپلیکیشن، فقط اطلاعات پایه حساب تلگرام شما (شناسه، نام، نام کاربری) دریافت می‌شود.</p>
            <p>۲. شماره موبایل فقط در صورت احراز هویت داوطلبانه (برای فعال‌سازی پاداش معرفی) ذخیره می‌شود.</p>
            <p>۳. اطلاعات پرداخت (رسید کارت‌به‌کارت) صرفاً برای تایید تراکنش نزد تیم پشتیبانی نگهداری می‌شود و در اختیار شخص ثالث قرار نمی‌گیرد.</p>
            <p>۴. اطلاعات مصرف حجم (میزان استفاده از سرویس) صرفاً برای نمایش وضعیت به خود شما و مدیریت فنی پنل استفاده می‌شود.</p>
            <p>۵. هیچ داده‌ای از فعالیت مرورگری یا محتوای ترافیک شما ذخیره یا بررسی نمی‌شود.</p>
          </div>
        )}
      </div>
    </div>
  );
}
