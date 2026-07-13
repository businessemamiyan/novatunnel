-- NovaTunnel — کاربران و درخت معرفی سه‌سطحی مشتری عادی
-- مرجع: NovaTunnel-Business-Rules.md بخش ۴، ۵، ۸

create table users (
  id uuid primary key default gen_random_uuid(),
  telegram_id bigint not null unique,
  telegram_username text,
  full_name text,
  phone_number text,
  phone_verified boolean not null default false,
  phone_verified_at timestamptz,
  referrer_id uuid references users(id) on delete set null,
  wallet_balance_toman numeric(14,0) not null default 0,
  gift_balance_gb numeric(12,3) not null default 0,
  last_purchase_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint users_no_self_referral check (referrer_id is distinct from id)
);

comment on column users.referrer_id is 'معرف مستقیم (سطح ۱). سیستم چندسطحی مشتری عادی (بخش ۴) با پیمایش این ستون تا ۳ سطح بالا محاسبه می‌شود.';
comment on column users.gift_balance_gb is 'موجودی جاری حجم هدیه، دنرمالایز از جمع gift_ledger.balance_after_gb — با trigger sync_gift_balance به‌روز می‌ماند.';
comment on column users.wallet_balance_toman is 'موجودی جاری کیف‌پول تومانی، دنرمالایز از wallet_transactions.balance_after_toman — با trigger sync_wallet_balance به‌روز می‌ماند.';
comment on column users.last_purchase_at is 'برای اجرای قانون سوختن حجم هدیه پس از ۴۰ روز بدون خرید (بخش ۵) استفاده می‌شود.';

create index idx_users_referrer_id on users(referrer_id);
create index idx_users_telegram_id on users(telegram_id);

create trigger trg_users_updated_at
before update on users
for each row execute function set_updated_at();

-- اجرای سقف حداکثر ۴ زیرمجموعه مستقیم برای هر معرف (بخش ۴، سطح ۱)
create or replace function enforce_max_direct_referrals()
returns trigger as $$
declare
  max_children int;
  current_count int;
begin
  if new.referrer_id is null then
    return new;
  end if;

  select max_direct_children into max_children
  from referral_level_config where level = 1;

  select count(*) into current_count
  from users
  where referrer_id = new.referrer_id
    and id <> new.id;

  if current_count >= max_children then
    raise exception 'کاربر % از قبل به حداکثر % زیرمجموعه مستقیم مجاز رسیده است (بخش ۴ سند قوانین)', new.referrer_id, max_children;
  end if;

  return new;
end;
$$ language plpgsql;

create trigger trg_enforce_max_direct_referrals
before insert or update of referrer_id on users
for each row execute function enforce_max_direct_referrals();

-- احراز موبایل شرط لازم برای هرگونه پاداش است (بخش ۸ — ضدتقلب)؛ رعایت این قانون در لایه محاسبه پاداش
-- (توابع/n8n) با شرط users.phone_verified = true انجام می‌شود، نه با محدودیت این جدول.
