-- NovaTunnel — لیست ادمین‌های ربات تلگرام (پشتیبانی چند-ادمین، بدون هاردکد در کد)
-- بخش خارج از سند قوانین اصلی: نیاز عملیاتی ربات برای مدیریت مشترک توسط چند نفر.

create table bot_admins (
  telegram_id bigint primary key,
  added_by bigint references bot_admins(telegram_id),
  is_active boolean not null default true,
  added_at timestamptz not null default now()
);

comment on table bot_admins is 'لیست سفید آیدی‌های تلگرام ادمین‌های ربات. جایگزین هاردکد ADMIN_CHAT_ID در کد شده.';

-- ادمین اولیه (bootstrap) — بدون این ردیف هیچ‌کس نمی‌تواند ادمین دیگری اضافه کند.
insert into bot_admins (telegram_id, added_by) values (7661530899, null);

alter table bot_admins enable row level security;
