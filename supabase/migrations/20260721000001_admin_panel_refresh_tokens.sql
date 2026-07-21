-- NovaTunnel — پنل مدیریت مستقل (Admin Panel v2, panel-api)
-- جدول جدید و additive؛ هیچ جدول موجودی تغییر نمی‌کند.
-- هویت ادمین همچنان از bot_admins گرفته می‌شود (Telegram Login Widget) — این جدول فقط
-- امکان ابطال/چرخش refresh token صادرشده برای پنل دسکتاپ را فراهم می‌کند.

create table admin_refresh_tokens (
  id uuid primary key default gen_random_uuid(),
  telegram_id bigint not null references bot_admins(telegram_id) on delete cascade,
  token_hash text not null unique,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz
);

comment on table admin_refresh_tokens is 'Refresh tokenهای صادرشده برای پنل مدیریت دسکتاپ (panel-api) — فقط hash ذخیره می‌شود، نه خود توکن.';

create index idx_admin_refresh_tokens_telegram_id on admin_refresh_tokens(telegram_id);
create index idx_admin_refresh_tokens_expires_at on admin_refresh_tokens(expires_at);

alter table admin_refresh_tokens enable row level security;
