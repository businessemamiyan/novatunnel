-- NovaTunnel — بسته آزمایشی رایگان (۵۰۰ مگ / ۲ ساعت / حذف خودکار از سرور)
-- مرجع: SESSION-LOG.md بخش ۱۵

alter table packages drop constraint packages_retail_price_toman_check;
alter table packages add constraint packages_retail_price_toman_check check (retail_price_toman >= 0);

alter table packages add column if not exists trial_hours integer;
comment on column packages.trial_hours is 'اگر مقداردار باشد، این بسته به‌جای اعتبار ۳۰ روزه استاندارد، فقط این تعداد ساعت اعتبار دارد و بعد از انقضا به‌صورت خودکار از سرور Marzban هم حذف می‌شود (نه فقط غیرفعال).';

alter table panels add column if not exists auto_delete_at timestamptz;
comment on column panels.auto_delete_at is 'فقط برای پنل‌های بسته آزمایشی — زمانی که یک job دوره‌ای باید این پنل را واقعاً از Marzban حذف کند، نه فقط غیرفعال.';
create index if not exists idx_panels_auto_delete_at on panels(auto_delete_at) where is_active;

alter table users add column if not exists trial_used_at timestamptz;
comment on column users.trial_used_at is 'زمان استفاده از بسته آزمایشی رایگان — هر کاربر فقط یک‌بار مجاز است.';

insert into packages (name, volume_gb, retail_price_toman, is_key_panel, is_active, trial_hours, badge)
select 'تست رایگان ۲ ساعته', 0.5, 0, false, true, 2, 'رایگان'
where not exists (select 1 from packages where trial_hours is not null);
