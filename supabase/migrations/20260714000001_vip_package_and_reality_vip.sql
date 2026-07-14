-- NovaTunnel — بسته ویژه (دسترسی به مسیر رله ایران در شرایط سخت)
-- مرجع: SESSION-LOG.md بخش ۱۴ — پروفایل «شرایط سخت» فقط برای خریداران بسته ویژه باز می‌شود، نه بسته‌های معمولی.

alter table packages add column if not exists is_vip boolean not null default false;

comment on column packages.is_vip is 'true یعنی خرید این بسته کاربر را به اینباند اختصاصی VLESS TCP REALITY VIP هم اضافه می‌کند (مسیر رله سرور ایران) — قیمت باید بالاتر از بسته معمولی هم‌حجم باشد.';

insert into packages (name, volume_gb, retail_price_toman, is_key_panel, is_vip, badge)
select '۳۰ گیگ ویژه 🛡', 30, 300000, false, true, 'ویژه'
where not exists (select 1 from packages where is_vip);
