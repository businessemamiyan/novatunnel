-- NovaTunnel — تغییر مدل panels از «یک پنل مشترک به‌ازای هر کاربر» به «هر خرید = یک سرویس مستقل»
-- تصمیم محصول (خارج از سند قوانین اصلی): هر خرید یک اکانت Marzban جدا با اسم دلخواه کاربر می‌سازد،
-- قابل تمدید/حذف مستقل، با اعتبار زمانی ۳۰ روزه از تاریخ خرید (علاوه بر سقف حجمی بسته).

alter table panels drop constraint panels_user_id_key;

alter table panels add column label text;
alter table panels add column purchase_id uuid references purchases(id);
alter table panels add column expires_at timestamptz;
alter table panels add column expiry_warned_at timestamptz;

comment on column panels.label is 'اسم دلخواهی که کاربر هنگام خرید برای این سرویس انتخاب کرده.';
comment on column panels.expires_at is 'تاریخ انقضای زمانی سرویس (۳۰ روز از تاریخ خرید) — مستقل از سقف حجمی بسته.';
comment on column panels.expiry_warned_at is 'زمان ارسال هشدار ۲۴ ساعت قبل از انقضا؛ برای جلوگیری از ارسال تکراری.';

create index idx_panels_expires_at on panels(expires_at) where is_active;

alter table purchases add column renewed_panel_id uuid references panels(id);
comment on column purchases.renewed_panel_id is 'اگر این خرید تمدید یک سرویس موجود باشد، به آن panel اشاره می‌کند؛ در غیر این صورت NULL (سرویس جدید).';
