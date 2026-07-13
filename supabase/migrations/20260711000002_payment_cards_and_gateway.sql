-- کارت‌های متعدد کارت‌به‌کارت (حداقل ۵ مجاز، تعداد نامحدود) + ستون‌های لازم برای درگاه آنلاین (زرین‌پال)

create table payment_cards (
  id serial primary key,
  card_number text not null,
  card_holder text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

alter table purchases add column if not exists gateway_authority text;
alter table wallet_topup_requests add column if not exists gateway_authority text;
alter table wallet_topup_requests add column if not exists payment_method payment_method default 'card_to_card';

alter table payment_cards enable row level security;
