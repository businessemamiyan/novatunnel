-- درخواست فعال‌سازی/ارتقای رده نمایندگی — مشابه wallet_topup_requests (کارت‌به‌کارت + تایید ادمین)
create table agency_activation_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  tier agency_tier not null,
  activation_fee_toman numeric(14,0) not null,
  upline_agent_id uuid references users(id),
  is_upgrade boolean not null default false,
  receipt_file_id text,
  status text not null default 'pending' check (status in ('pending', 'confirmed', 'rejected')),
  created_at timestamptz not null default now(),
  confirmed_at timestamptz
);

create index idx_agency_activation_requests_user on agency_activation_requests(user_id);

comment on table agency_activation_requests is 'درخواست فعال‌سازی یا ارتقای رده نمایندگی، در انتظار تایید ادمین (بخش ۶.۲).';

alter table agency_activation_requests enable row level security;

-- زیرمجموعه کامل زنجیره یک نماینده (همه نمایندگانی که مستقیم یا غیرمستقیم توسط او معرفی شده‌اند)
create or replace function get_agency_downline_ids(p_agent_id uuid)
returns table(agent_id uuid, tier agency_tier, level int)
language sql
stable
as $$
  with recursive downline as (
    select at.user_id as agent_id, at.tier, 1 as level
    from agency_tiers at
    where at.upline_agent_id = p_agent_id

    union all

    select at2.user_id, at2.tier, d.level + 1
    from downline d
    join agency_tiers at2 on at2.upline_agent_id = d.agent_id
  )
  select * from downline;
$$;

comment on function get_agency_downline_ids(uuid) is 'برای نمایش زیرمجموعه نمایندگی (مستقیم+غیرمستقیم) در داشبورد نماینده.';
