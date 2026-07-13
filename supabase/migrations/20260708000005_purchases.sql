-- NovaTunnel — خریدها (خرده‌فروشی مالک و فروش نماینده)
-- مرجع: NovaTunnel-Business-Rules.md بخش ۳، ۵، ۶.۶، ۷

create table purchases (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  package_id smallint references packages(id),
  seller_type seller_type not null default 'owner',
  seller_agent_id uuid references users(id),
  volume_gb numeric(10,2) not null check (volume_gb > 0),
  price_toman numeric(14,0) not null check (price_toman >= 0),
  is_gift_resale boolean not null default false,
  payment_method payment_method,
  payment_status payment_status not null default 'pending',
  purchased_at timestamptz not null default now(),
  confirmed_at timestamptz,
  constraint purchases_seller_agent_required check (
    (seller_type = 'owner' and seller_agent_id is null) or
    (seller_type = 'agent' and seller_agent_id is not null)
  )
);

comment on column purchases.is_gift_resale is 'true وقتی نماینده حجم هدیه‌ای که خودش رایگان دریافت کرده را می‌فروشد (بخش ۶.۶) — این خریدها مشمول کف قیمت ۴۰۰۰ تومان نیستند.';
comment on column purchases.package_id is 'برای فروش سفارشی نماینده (حجم/قیمت دلخواه) می‌تواند NULL باشد.';

create index idx_purchases_user_id on purchases(user_id);
create index idx_purchases_seller_agent_id on purchases(seller_agent_id);
create index idx_purchases_status on purchases(payment_status);

-- کف قیمت فروش نماینده: هرگز کمتر از کف خرده‌فروشی مالک (بخش ۷). فروش حجم هدیه رایگان از این قانون معاف است.
create or replace function enforce_resale_price_floor()
returns trigger as $$
declare
  floor_price numeric;
  per_gb_price numeric;
begin
  if new.seller_type = 'agent' and new.is_gift_resale = false then
    select value into floor_price from system_settings where key = 'min_resale_price_toman_per_gb';
    per_gb_price := new.price_toman / new.volume_gb;
    if per_gb_price < floor_price then
      raise exception 'قیمت فروش نماینده (% تومان/گیگ) کمتر از کف مجاز % تومان است (بخش ۷ سند قوانین)', round(per_gb_price), round(floor_price);
    end if;
  end if;
  return new;
end;
$$ language plpgsql;

create trigger trg_enforce_resale_price_floor
before insert or update on purchases
for each row execute function enforce_resale_price_floor();

-- خرید تایید شده، last_purchase_at را به‌روزرسانی می‌کند (مبنای قانون سوختن ۴۰ روزه، بخش ۵)
-- دو trigger جدا برای INSERT و UPDATE تا نیازی به دسترسی به OLD در حالت INSERT نباشد.
create or replace function update_last_purchase_at_on_insert()
returns trigger as $$
begin
  if new.payment_status = 'confirmed' then
    update users set last_purchase_at = coalesce(new.confirmed_at, now()), updated_at = now()
    where id = new.user_id;
  end if;
  return new;
end;
$$ language plpgsql;

create trigger trg_purchases_last_purchase_at_insert
after insert on purchases
for each row execute function update_last_purchase_at_on_insert();

create or replace function update_last_purchase_at_on_update()
returns trigger as $$
begin
  if new.payment_status = 'confirmed' and old.payment_status is distinct from 'confirmed' then
    update users set last_purchase_at = coalesce(new.confirmed_at, now()), updated_at = now()
    where id = new.user_id;
  end if;
  return new;
end;
$$ language plpgsql;

create trigger trg_purchases_last_purchase_at_update
after update of payment_status on purchases
for each row execute function update_last_purchase_at_on_update();
