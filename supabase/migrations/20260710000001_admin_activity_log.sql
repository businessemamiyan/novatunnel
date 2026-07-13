-- NovaTunnel — لاگ فعالیت ادمین‌ها (Mini App پنل مدیریت) و نگهداری عکس رسید کارت‌به‌کارت
-- خارج از سند قوانین اصلی: نیاز عملیاتی پنل مدیریت.

create table admin_activity_log (
  id uuid primary key default gen_random_uuid(),
  admin_telegram_id bigint not null,
  action_type text not null,
  target_description text,
  metadata jsonb,
  created_at timestamptz not null default now()
);

comment on table admin_activity_log is 'هر اقدام مهم ادمین (تایید/رد رسید، حذف/تمدید سرویس، تغییر قیمت، Broadcast) اینجا ثبت می‌شود.';
comment on column admin_activity_log.action_type is 'مثلا: receipt_approve, receipt_reject, service_delete, service_renew, package_price_update, broadcast_sent, admin_add, admin_remove';

create index idx_admin_activity_log_created_at on admin_activity_log(created_at desc);
create index idx_admin_activity_log_admin on admin_activity_log(admin_telegram_id);

alter table admin_activity_log enable row level security;

-- برای نمایش عکس رسید در پنل ادمین Mini App (فعلاً فقط در چت تلگرام بین ربات و ادمین رد و بدل می‌شد، جایی ذخیره نمی‌شد)
alter table purchases add column receipt_file_id text;
comment on column purchases.receipt_file_id is 'file_id تلگرام عکس رسید کارت‌به‌کارت؛ برای نمایش در پنل ادمین از طریق Bot API getFile پروکسی می‌شود.';
