-- NovaTunnel — سیستم نمایندگی سه‌رده و زنجیره تک‌شاخه‌ای
-- مرجع: NovaTunnel-Business-Rules.md بخش ۶

create table agency_tiers (
  user_id uuid primary key references users(id) on delete cascade,
  tier agency_tier not null,
  upline_agent_id uuid references users(id) on delete set null,
  activation_fee_paid_toman numeric(14,0) not null,
  purchase_rate_toman_per_gb numeric(10,0) not null,
  min_wallet_balance_toman numeric(14,0) not null,
  is_panel_active boolean not null default true,
  activated_at timestamptz not null default now(),
  last_upgraded_at timestamptz,
  constraint agency_no_self_upline check (upline_agent_id is distinct from user_id),
  -- زنجیره تک‌شاخه‌ای (بخش ۶.۵): هر نماینده حداکثر توسط یک نماینده دیگر معرفی می‌شود،
  -- پس هر upline_agent_id باید در کل جدول یکتا باشد (NULL چندباره مجاز است — نمایندگان ریشه).
  constraint agency_tiers_upline_unique unique (upline_agent_id)
);

comment on table agency_tiers is 'زنجیره نمایندگی از طریق upline_agent_id پیاده‌سازی شده؛ نیازی به جدول جداگانه agency_chain نیست چون رابطه ۱-به-۱ است.';
comment on column agency_tiers.activation_fee_paid_toman is 'مبلغ فعال‌سازی/ارتقا snapshot شده — جدا از کیف‌پول خرید حجم، صرف زیرساخت می‌شود و به کیف‌پول واریز نمی‌گردد (بخش ۶.۲).';
comment on column agency_tiers.purchase_rate_toman_per_gb is 'نرخ خرید هر گیگ در لحظه فعال‌سازی/آخرین ارتقا snapshot شده تا تغییر بعدی agency_tier_config روی تعهدات فعلی اثر نگذارد.';
comment on column agency_tiers.is_panel_active is 'اگر موجودی کیف‌پول نماینده (users.wallet_balance_toman) کمتر از min_wallet_balance_toman شود، باید false شود (بخش ۶.۳).';

create index idx_agency_tiers_upline on agency_tiers(upline_agent_id);
create index idx_agency_tiers_tier on agency_tiers(tier);

-- هنگام فعال‌سازی/ارتقا، اگر موجودی فعلی کیف‌پول کمتر از حداقل رده جدید است، پنل را غیرفعال علامت بزن
create or replace function sync_agency_panel_active_state()
returns trigger as $$
declare
  wallet numeric;
begin
  select wallet_balance_toman into wallet from users where id = new.user_id;
  new.is_panel_active := (wallet >= new.min_wallet_balance_toman);
  return new;
end;
$$ language plpgsql;

create trigger trg_agency_tiers_panel_state
before insert or update of min_wallet_balance_toman on agency_tiers
for each row execute function sync_agency_panel_active_state();
