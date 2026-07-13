-- درخواست شارژ کیف‌پول از داخل Mini App/ربات (کارت‌به‌کارت با تایید ادمین)

create table wallet_topup_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  amount_toman numeric(14,0) not null check (amount_toman > 0),
  status text not null default 'pending' check (status in ('pending', 'confirmed', 'rejected')),
  created_at timestamptz not null default now(),
  confirmed_at timestamptz
);

create index idx_wallet_topup_user on wallet_topup_requests(user_id);
create index idx_wallet_topup_status on wallet_topup_requests(status);

alter table wallet_topup_requests enable row level security;
