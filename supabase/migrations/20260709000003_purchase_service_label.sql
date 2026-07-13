-- NovaTunnel — نگهداری اسم دلخواه سرویس که کاربر هنگام خرید انتخاب می‌کند
-- تا وقتی ادمین پرداخت را تایید می‌کند و panel واقعی ساخته می‌شود، این مقدار روی purchases نگه داشته می‌شود.

alter table purchases add column service_label text;
