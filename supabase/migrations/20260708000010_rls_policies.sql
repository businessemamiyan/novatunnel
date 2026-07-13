-- NovaTunnel — فعال‌سازی RLS روی جداول اصلی کسب‌وکار
-- مرجع: NovaTunnel-Business-Rules.md بخش ۲ (ربات تلگرام + Mini App به‌عنوان کلاینت)
--
-- توجه مهم: احراز هویت این پروژه بر پایه Telegram است، نه Supabase Auth. تا زمانی که پل بین
-- Telegram initData و JWT توکن Supabase (مثلا از طریق یک Edge Function صادرکننده JWT سفارشی)
-- طراحی و نهایی نشود، این migration به‌صورت عمدی هیچ policy مجازی برای anon/authenticated تعریف نمی‌کند.
-- یعنی این جداول با کلید service_role (که RLS را دور می‌زند) توسط ربات تلگرام/n8n/Edge Functions
-- خوانده و نوشته می‌شوند؛ کلاینت Mini App نباید مستقیم با کلید anon به این جداول دسترسی داشته باشد
-- تا زمانی که policyهای دقیق بر اساس مدل احراز هویت نهایی نوشته شود.

alter table users enable row level security;
alter table agency_tiers enable row level security;
alter table purchases enable row level security;
alter table wallet_transactions enable row level security;
alter table gift_ledger enable row level security;
alter table panels enable row level security;
