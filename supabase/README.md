# دیتابیس NovaTunnel — Supabase

این پوشه شامل migrationهای SQL برای دیتابیس PostgreSQL پروژه در Supabase است. طراحی این جداول
مستقیماً از [`../NovaTunnel-Business-Rules.md`](../NovaTunnel-Business-Rules.md) استخراج شده؛ هر
تغییر در قوانین کسب‌وکار باید اول در آن سند و سپس در یک migration جدید اعمال شود (هرگز فایل‌های
موجود را ویرایش نکنید — یک migration جدید اضافه کنید).

## ترتیب فایل‌ها

| فایل | محتوا |
|---|---|
| `20260708000001_extensions_and_types.sql` | افزونه pgcrypto، enumها، تابع `set_updated_at()` |
| `20260708000002_reference_config_tables.sql` | `packages`، `agency_tier_config`، `referral_level_config`، `system_settings` + seed |
| `20260708000003_users_and_referrals.sql` | `users` + سقف ۴ زیرمجموعه مستقیم |
| `20260708000004_agency_tiers.sql` | `agency_tiers` + زنجیره تک‌شاخه‌ای نمایندگی |
| `20260708000005_purchases.sql` | `purchases` + کف قیمت فروش نماینده + به‌روزرسانی `last_purchase_at` |
| `20260708000006_wallet_transactions.sql` | `wallet_transactions` + همگام‌سازی موجودی کیف‌پول |
| `20260708000007_gift_ledger.sql` | `gift_ledger` + همگام‌سازی موجودی حجم هدیه + تابع سوختن ۴۰ روزه |
| `20260708000008_panels.sql` | `panels` (Marzban/X-ui) |
| `20260708000009_reward_helper_functions.sql` | توابع کمکی محاسبه پاداش (بالادست سطح ۱-۳، زنجیره نمایندگی) |
| `20260708000010_rls_policies.sql` | فعال‌سازی RLS روی جداول اصلی |

## اجرا

در این محیط توسعه، Node/npm و Supabase CLI نصب نیستند؛ فقط Docker موجود است. دو راه برای اجرا:

**۱) SQL Editor داشبورد Supabase (سریع‌ترین راه فعلی)**
فایل‌ها را به ترتیب شماره در SQL Editor پروژه Supabase خود paste و اجرا کنید.

**۲) نصب Supabase CLI (توصیه‌شده برای ادامه کار تیمی)**
```
scoop install supabase   # یا نصب باینری از GitHub releases
supabase login
supabase link --project-ref <project-ref>
supabase db push
```

## نکات مهم پیاده‌سازی

- **موتور محاسبه پاداش در این migrationها ساخته نشده** — طبق معماری سند قوانین (بخش ۲)، محاسبه
  فن‌اوت پاداش سطحی/نمایندگی و اعمال سقف‌ها باید در ورک‌فلوهای n8n پیاده شود؛ این migrationها فقط
  جداول، محدودیت‌ها، تریگرهای ثابت (سقف زیرمجموعه، کف قیمت، همگام‌سازی موجودی) و توابع کمکی SQL
  (`get_referral_ancestors`, `get_agency_upline_ids`) را فراهم می‌کنند.
- `expire_stale_gift_balances()` باید روزانه از طریق `pg_cron` یا زمان‌بند n8n فراخوانی شود — خودکار
  اجرا نمی‌شود.
- RLS روی جداول اصلی فعال است اما **بدون هیچ policy مجاز** برای `anon`/`authenticated`، چون پل بین
  احراز هویت Telegram و JWT توکن Supabase هنوز طراحی نشده. فعلاً همه خواندن/نوشتن باید با
  `service_role` (از طریق n8n/Edge Function) انجام شود.
