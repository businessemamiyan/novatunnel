-- NovaTunnel — سیستم حسابداری ساده (هزینه‌ها) برای پنل ادمین و پنل نمایندگی
-- مرجع: پرامپت-کلاد-کد-پنل-ادمین-حسابداری.md

create table expenses (
  id uuid primary key default gen_random_uuid(),
  agent_id uuid references users(id) on delete cascade,
  amount_toman numeric(14,0) not null check (amount_toman > 0),
  description text not null,
  category text,
  created_by_telegram_id bigint not null,
  created_at timestamptz not null default now()
);

comment on column expenses.agent_id is 'NULL یعنی هزینه کلی کسب‌وکار (پنل حسابداری ادمین)؛ مقداردار یعنی هزینه شخصی همان نماینده (پنل حسابداری نمایندگی خودش) — دو دفتر کاملاً جدا.';

create index idx_expenses_agent_id on expenses(agent_id);
create index idx_expenses_created_at on expenses(created_at);

alter table expenses enable row level security;
