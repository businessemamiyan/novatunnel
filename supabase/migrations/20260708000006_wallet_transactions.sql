-- NovaTunnel — دفتر کل تراکنش‌های کیف‌پول تومانی
-- مرجع: NovaTunnel-Business-Rules.md بخش ۶.۲، ۶.۳

create table wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  type wallet_tx_type not null,
  amount_toman numeric(14,0) not null,
  balance_after_toman numeric(14,0) not null,
  reference_purchase_id uuid references purchases(id),
  payment_method payment_method,
  note text,
  created_at timestamptz not null default now(),
  constraint wallet_tx_balance_non_negative check (balance_after_toman >= 0)
);

comment on column wallet_transactions.amount_toman is 'مثبت برای شارژ/بازگشت وجه، منفی برای برداشت (خرید، هزینه فعال‌سازی/ارتقای نمایندگی). balance_after_toman باید مبلغ قبلی + amount_toman باشد؛ محاسبه بر عهده لایه فراخوان (n8n/edge function) است.';

create index idx_wallet_tx_user_id on wallet_transactions(user_id);
create index idx_wallet_tx_created_at on wallet_transactions(created_at);

-- موجودی کیف‌پول کاربر را دنرمالایز و همگام نگه می‌دارد
create or replace function sync_wallet_balance()
returns trigger as $$
begin
  update users set wallet_balance_toman = new.balance_after_toman, updated_at = now()
  where id = new.user_id;

  -- اگر کاربر نماینده است، وضعیت فعال/غیرفعال پنل را بر اساس حداقل موجودی رده‌اش به‌روز کن (بخش ۶.۳)
  update agency_tiers
  set is_panel_active = (new.balance_after_toman >= min_wallet_balance_toman)
  where user_id = new.user_id;

  return new;
end;
$$ language plpgsql;

create trigger trg_wallet_tx_sync_balance
after insert on wallet_transactions
for each row execute function sync_wallet_balance();
