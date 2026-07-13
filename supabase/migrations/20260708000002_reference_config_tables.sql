-- NovaTunnel — جداول مرجع/پیکربندی
-- این جداول تک منبع حقیقت اعداد قوانین کسب‌وکارند تا در کد/n8n هاردکد نشوند.
-- مرجع: NovaTunnel-Business-Rules.md بخش‌های ۳، ۴، ۶.۱، ۷، ۱۰

-- بسته‌های خرده‌فروشی مالک (بخش ۳)
create table packages (
  id smallint generated always as identity primary key,
  name text not null,
  volume_gb numeric(10,2) not null check (volume_gb > 0),
  retail_price_toman numeric(14,0) not null check (retail_price_toman > 0),
  is_key_panel boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

comment on column packages.is_key_panel is 'true فقط برای بسته ۵ گیگ که خرید آن قفل مصرف حجم هدیه انباشته‌شده کاربر را باز می‌کند (بخش ۵ سند قوانین).';

insert into packages (name, volume_gb, retail_price_toman, is_key_panel) values
  ('پنل کلید ۵ گیگ', 5, 20000, true),
  ('۳۰ گیگ', 30, 200000, false),
  ('۵۰ گیگ', 50, 250000, false),
  ('۱۰۰ گیگ', 100, 400000, false);

-- نرخ‌های رده نمایندگی (بخش ۶.۱). هر ردیف در agency_tiers هنگام فعال‌سازی/ارتقا از این جدول snapshot می‌گیرد
-- تا تغییر بعدی نرخ‌ها، تعهدات نمایندگان فعلی را تحت تاثیر قرار ندهد.
create table agency_tier_config (
  tier agency_tier primary key,
  activation_fee_toman numeric(14,0) not null,
  purchase_rate_toman_per_gb numeric(10,0) not null,
  min_wallet_balance_toman numeric(14,0) not null,
  updated_at timestamptz not null default now()
);

insert into agency_tier_config (tier, activation_fee_toman, purchase_rate_toman_per_gb, min_wallet_balance_toman) values
  ('silver', 1500000, 3000, 500000),
  ('gold', 3000000, 2500, 1000000),
  ('diamond', 10000000, 1500, 2500000);

-- پیکربندی سطوح سیستم چندسطحی مشتری عادی (بخش ۴)
-- توجه: فقط max_direct_children سطح ۱ به‌صورت trigger روی users enforce می‌شود؛
-- اعداد سطح ۲ و ۳ (۱۶ و ۶۴) نتیجه ریاضی انشعاب ۴تایی سطح ۱ هستند و صرفا جهت مرجع/گزارش‌گیری ذخیره می‌شوند.
create table referral_level_config (
  level smallint primary key check (level in (1, 2, 3)),
  max_direct_children int not null,
  reward_percent numeric(5,2) not null,
  monthly_cap_gb numeric(10,2) not null
);

insert into referral_level_config (level, max_direct_children, reward_percent, monthly_cap_gb) values
  (1, 4, 5, 30),
  (2, 16, 3, 30),
  (3, 64, 1, 40);

-- ثابت‌های سراسری سیستم (بخش ۳، ۵، ۶.۵، ۷، ۱۰)
create table system_settings (
  key text primary key,
  value numeric not null,
  description text
);

insert into system_settings (key, value, description) values
  ('owner_cost_toman_per_gb', 1000, 'هزینه واقعی هر گیگابایت برای مالک سیستم'),
  ('min_resale_price_toman_per_gb', 4000, 'کف مطلق قیمت فروش حجم برای همه — مالک و نماینده'),
  ('customer_monthly_cap_gb', 100, 'سقف مطلق ماهانه پاداش حجم هدیه برای مشتری عادی'),
  ('gift_volume_expiry_days', 40, 'اگر ظرف این تعداد روز از آخرین خرید، خرید جدیدی ثبت نشود، کل حجم هدیه انباشته صفر می‌شود'),
  ('agency_period_days', 50, 'طول بازه محاسبه سقف پاداش زنجیره نمایندگی'),
  ('agency_period_cap_gb', 300, 'سقف مطلق پاداش هر نماینده در هر بازه agency_period_days'),
  ('agency_chain_reward_percent', 1, 'درصد پاداش حجمی که هر نماینده از کل زیرمجموعه زنجیره‌اش دریافت می‌کند');

alter table packages enable row level security;
alter table agency_tier_config enable row level security;
alter table referral_level_config enable row level security;
alter table system_settings enable row level security;

create policy "public read packages" on packages for select using (true);
create policy "public read agency_tier_config" on agency_tier_config for select using (true);
create policy "public read referral_level_config" on referral_level_config for select using (true);
create policy "public read system_settings" on system_settings for select using (true);
