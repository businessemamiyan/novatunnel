-- NovaTunnel — اصلاح مدل «ویژه» به یک افزونه (نه جایگزین رده) + پرچم تراکنش تست/رایگان
-- مرجع: SESSION-LOG.md بخش ۱۴.۱ (نسخه اصلاح‌شده)

-- ویژه دیگر یک رده جایگزین نیست — یک قفل اضافه روی رده فعلی نماینده است.
-- نرخ ۶۰۰۰ت فقط برای حجمی که صراحتاً «ویژه» فروخته می‌شود اعمال می‌شود؛ بقیه فروش نماینده
-- با همان نرخ رده فعلی‌اش (نقره‌ای/طلایی/برلیان) محاسبه می‌شود، نه با نرخ ویژه.
alter table agency_tiers add column if not exists vip_unlocked boolean not null default false;
alter table agency_tiers add column if not exists vip_activated_at timestamptz;

comment on column agency_tiers.vip_unlocked is 'true یعنی نماینده هزینه فعال‌سازی ویژه (agency_tier_config کلید vip) را پرداخته و می‌تواند سرویس ویژه بفروشد — رده اصلی‌اش (silver/gold/diamond) دست‌نخورده می‌ماند و نرخ خرید حجم معمولی‌اش عوض نمی‌شود.';

-- برای حذف تراکنش‌های تست/رایگان از محاسبه سود و زیان
alter table purchases add column if not exists is_test boolean not null default false;
comment on column purchases.is_test is 'true یعنی این خرید/سرویس یک تست یا هدیه اداری است و نباید در آمار فروش/حسابداری لحاظ شود.';
