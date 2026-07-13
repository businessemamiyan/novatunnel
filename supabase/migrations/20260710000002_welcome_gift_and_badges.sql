-- هدیه خوش‌آمدگویی فوری کیف‌پول برای ثبت‌نام جدید + برچسب کیفی بسته‌ها
-- مرجع: NovaTunnel-Business-Rules.md — بخش جدید «هدیه خوش‌آمدگویی» زیر سیستم ۳سطحی مشتری عادی

alter type wallet_tx_type add value if not exists 'initial_join_gift';

alter table purchases add column if not exists wallet_credit_used_toman numeric(14,0) not null default 0;

alter table packages add column if not exists badge text;

update packages set badge = 'پنل کلید' where volume_gb = 5;
update packages set badge = 'اقتصادی' where volume_gb = 30;
update packages set badge = 'محبوب' where volume_gb = 50;
update packages set badge = 'پرمصرف' where volume_gb = 100;
