-- شناسه کوتاه متنی برای لینک اختصاصی نماینده (فقط در URL دیده می‌شود، به مشتری نمایش داده نمی‌شود)
alter table agency_tiers add column if not exists agent_slug text unique;
alter table agency_tiers add column if not exists custom_pricing_enabled boolean not null default true;
alter table agency_tiers add column if not exists support_contact text;

-- اتصال دائمی مشتری به نماینده (فقط برای محاسبه قیمت/فروش — جدا از users.referrer_id که برای پاداش چندسطحی مشتری عادی است)
create table customer_agent_binding (
  customer_user_id uuid primary key references users(id),
  agent_id uuid not null references users(id),
  bound_at timestamptz not null default now()
);

create index idx_customer_agent_binding_agent on customer_agent_binding(agent_id);

comment on table customer_agent_binding is 'اتصال immutable مشتری به نماینده‌ای که از لینک اختصاصی‌اش وارد شده — فقط برای قیمت‌گذاری/دفتر فروش، بدون تغییر در برند/تجربه کاربر.';

-- قیمت‌گذاری اختصاصی نماینده روی هر بسته (در بازه مجاز: کف = هزینه خرید خودش، سقف = طبق system_settings)
create table agent_plan_pricing (
  id uuid primary key default gen_random_uuid(),
  agent_id uuid not null references users(id),
  package_id smallint not null references packages(id),
  retail_price_toman numeric(14,0) not null,
  updated_at timestamptz not null default now(),
  unique (agent_id, package_id)
);

insert into system_settings (key, value, description) values
  ('agent_custom_pricing_max_markup_percent', 100, 'حداکثر درصد سود مجاز نماینده هنگام قیمت‌گذاری دستی روی بسته‌ها (نسبت به هزینه خرید خودش)')
on conflict (key) do nothing;
