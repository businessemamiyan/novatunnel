-- NovaTunnel — کدهای تخفیف (نیاز جدید ربات تلگرام، خارج از سند قوانین اصلی)
-- کد تخفیف مستقل از سیستم پاداش حجم هدیه است: روی قیمت تومانی خرید از فروشگاه ربات اثر می‌گذارد،
-- نه روی حجم هدیه چندسطحی.

create table discount_codes (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  discount_type text not null check (discount_type in ('percent', 'fixed_toman')),
  discount_value numeric(10,2) not null check (discount_value > 0),
  max_uses int,
  used_count int not null default 0,
  max_uses_per_user int not null default 1,
  min_purchase_toman numeric(14,0) not null default 0,
  expires_at timestamptz,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  constraint discount_percent_range check (
    discount_type <> 'percent' or (discount_value > 0 and discount_value <= 100)
  )
);

comment on column discount_codes.code is 'همیشه با حروف بزرگ ذخیره می‌شود (نرمال‌سازی در لایه اپلیکیشن/ربات انجام می‌شود).';
comment on column discount_codes.max_uses is 'NULL یعنی بدون محدودیت تعداد کل استفاده.';

create index idx_discount_codes_code on discount_codes(code) where is_active;

-- ثبت هر بار استفاده از کد، هم برای audit و هم جلوگیری از سواستفاده تکراری یک کاربر
create table discount_code_redemptions (
  id uuid primary key default gen_random_uuid(),
  code_id uuid not null references discount_codes(id),
  user_id uuid not null references users(id),
  purchase_id uuid references purchases(id),
  discount_amount_toman numeric(14,0) not null,
  redeemed_at timestamptz not null default now(),
  -- پیش‌فرض max_uses_per_user=1 در discount_codes؛ این محدودیت همان حالت رایج را در دیتابیس enforce می‌کند.
  constraint discount_code_redemptions_unique_per_user unique (code_id, user_id)
);

create index idx_discount_redemptions_code on discount_code_redemptions(code_id);
create index idx_discount_redemptions_user on discount_code_redemptions(user_id);

-- ردیابی راحت تخفیف اعمال‌شده روی هر خرید (دنرمالایز، برای نمایش سریع در ربات/گزارش‌گیری)
alter table purchases add column discount_code_id uuid references discount_codes(id);
alter table purchases add column discount_amount_toman numeric(14,0) not null default 0;

-- افزایش خودکار used_count هنگام ثبت هر redemption
create or replace function increment_discount_code_usage()
returns trigger as $$
begin
  update discount_codes set used_count = used_count + 1 where id = new.code_id;
  return new;
end;
$$ language plpgsql;

create trigger trg_discount_code_redemption_increment
after insert on discount_code_redemptions
for each row execute function increment_discount_code_usage();

alter table discount_codes enable row level security;
alter table discount_code_redemptions enable row level security;
