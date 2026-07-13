-- NovaTunnel — دفتر کل حجم هدیه (پاداش‌های چندسطحی و زنجیره نمایندگی)
-- مرجع: NovaTunnel-Business-Rules.md بخش ۴، ۵، ۶.۵

create table gift_ledger (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  entry_type gift_ledger_entry_type not null,
  level smallint check (level in (1, 2, 3)),
  source_purchase_id uuid references purchases(id),
  source_user_id uuid references users(id),
  gross_calculated_gb numeric(12,3),
  amount_gb numeric(12,3) not null,
  balance_after_gb numeric(12,3) not null,
  note text,
  created_at timestamptz not null default now(),
  constraint gift_ledger_balance_non_negative check (balance_after_gb >= 0),
  constraint gift_ledger_level_only_for_customer_rewards check (
    (entry_type in ('credit_level_1', 'credit_level_2', 'credit_level_3') and level is not null) or
    (entry_type not in ('credit_level_1', 'credit_level_2', 'credit_level_3') and level is null)
  )
);

comment on column gift_ledger.gross_calculated_gb is 'مقدار پاداش پیش از برش توسط سقف سطح/ماهانه — برای حسابرسی مقدار «حذف‌شده» طبق بخش ۴ سند قوانین.';
comment on column gift_ledger.amount_gb is 'مثبت برای credit (پاداش)، منفی برای debit (مصرف/سوختن). balance_after_gb = موجودی قبلی + amount_gb، محاسبه بر عهده لایه فراخوان است.';
comment on column gift_ledger.source_user_id is 'کاربری که با خریدش باعث این پاداش شده (زیرمجموعه سطح ۱/۲/۳ یا عضو زنجیره نمایندگی).';

create index idx_gift_ledger_user_id on gift_ledger(user_id);
create index idx_gift_ledger_source_purchase on gift_ledger(source_purchase_id);

create or replace function sync_gift_balance()
returns trigger as $$
begin
  update users set gift_balance_gb = new.balance_after_gb, updated_at = now()
  where id = new.user_id;
  return new;
end;
$$ language plpgsql;

create trigger trg_gift_ledger_sync_balance
after insert on gift_ledger
for each row execute function sync_gift_balance();

-- قانون سوختن ۴۰ روزه (بخش ۵): اگر ظرف gift_volume_expiry_days روز از آخرین خرید، خرید جدیدی ثبت نشود،
-- کل موجودی حجم هدیه کاربر صفر می‌شود. این تابع باید روزانه از طریق pg_cron یا زمان‌بند n8n فراخوانی شود.
create or replace function expire_stale_gift_balances()
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  expiry_days int;
  rec record;
begin
  select value::int into expiry_days from system_settings where key = 'gift_volume_expiry_days';

  for rec in
    select id, gift_balance_gb
    from users
    where gift_balance_gb > 0
      and last_purchase_at is not null
      and last_purchase_at < now() - (expiry_days || ' days')::interval
  loop
    insert into gift_ledger (user_id, entry_type, amount_gb, balance_after_gb, note)
    values (
      rec.id,
      'debit_expired',
      -rec.gift_balance_gb,
      0,
      format('سوخت خودکار حجم هدیه پس از %s روز بدون خرید (بخش ۵ سند قوانین)', expiry_days)
    );
  end loop;
end;
$$;

comment on function expire_stale_gift_balances() is 'باید روزانه از طریق pg_cron (در صورت فعال بودن افزونه در Supabase) یا یک workflow زمان‌بندی‌شده n8n فراخوانی شود.';
