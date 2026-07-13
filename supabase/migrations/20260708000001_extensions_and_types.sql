-- NovaTunnel — افزونه‌ها و انواع پایه
-- مرجع: NovaTunnel-Business-Rules.md

create extension if not exists "pgcrypto"; -- برای gen_random_uuid()

create type agency_tier as enum ('silver', 'gold', 'diamond');

create type payment_method as enum ('zarinpal', 'card_to_card', 'crypto');

create type payment_status as enum ('pending', 'confirmed', 'failed', 'refunded');

create type seller_type as enum ('owner', 'agent');

-- انواع تراکنش کیف‌پول تومانی (بخش ۶.۲ و ۷ سند قوانین)
create type wallet_tx_type as enum (
  'topup',
  'purchase_debit',
  'agency_activation_fee',
  'agency_upgrade_fee',
  'gift_resale_credit',
  'refund'
);

-- انواع رویداد دفتر کل حجم هدیه (بخش ۴، ۵ و ۶.۵ سند قوانین)
create type gift_ledger_entry_type as enum (
  'credit_level_1',
  'credit_level_2',
  'credit_level_3',
  'credit_agency_chain',
  'debit_consumption',
  'debit_expired'
);

-- تابع عمومی برای به‌روزرسانی خودکار updated_at
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;
