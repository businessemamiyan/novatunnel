-- NovaTunnel — توابع کمکی محاسبه پاداش (برای فراخوانی از n8n/Edge Functions هنگام ثبت خرید)
-- مرجع: NovaTunnel-Business-Rules.md بخش ۴، ۶.۵، ۸
-- این توابع فقط داده لازم برای محاسبه پاداش را برمی‌گردانند؛ منطق سقف‌گذاری و ثبت gift_ledger
-- در لایه ارکستراسیون (n8n) پیاده می‌شود تا با معماری اتوماسیون سند قوانین (بخش ۲) همسو بماند.

-- بالادست‌های سطح ۱ تا ۳ یک کاربر در درخت معرفی مشتری عادی، به‌همراه وضعیت احراز موبایل هرکدام.
-- بخش ۸: پاداش فقط برای معرف احراز هویت‌شده با موبایل محاسبه می‌شود — لایه فراخوان باید phone_verified را چک کند.
create or replace function get_referral_ancestors(p_user_id uuid)
returns table(level smallint, ancestor_id uuid, phone_verified boolean)
language sql
stable
as $$
  with recursive ancestors as (
    select 1::smallint as level, u.referrer_id as ancestor_id
    from users u
    where u.id = p_user_id and u.referrer_id is not null

    union all

    select (a.level + 1)::smallint, u.referrer_id
    from ancestors a
    join users u on u.id = a.ancestor_id
    where a.level < 3 and u.referrer_id is not null
  )
  select a.level, a.ancestor_id, u.phone_verified
  from ancestors a
  join users u on u.id = a.ancestor_id;
$$;

-- کل زنجیره بالادست نمایندگی یک نماینده، بدون محدودیت عمق (بخش ۶.۵).
-- چون زنجیره تک‌شاخه‌ای است (هر نماینده دقیقا یک upline دارد)، این پیمایش یک لیست پیوندی ساده و بدون انشعاب است.
create or replace function get_agency_upline_ids(p_agent_id uuid)
returns table(upline_agent_id uuid)
language sql
stable
as $$
  with recursive chain as (
    select at.upline_agent_id
    from agency_tiers at
    where at.user_id = p_agent_id and at.upline_agent_id is not null

    union all

    select at2.upline_agent_id
    from chain c
    join agency_tiers at2 on at2.user_id = c.upline_agent_id
    where at2.upline_agent_id is not null
  )
  select * from chain;
$$;

comment on function get_referral_ancestors(uuid) is 'برای هر خرید تایید شده فراخوانی شود تا پاداش سطح ۱/۲/۳ به بالادست‌های احراز هویت‌شده تعلق گیرد.';
comment on function get_agency_upline_ids(uuid) is 'برای هر خرید زیر چتر یک نماینده فراخوانی شود تا پاداش ۱٪ به همه نمایندگان بالادست زنجیره تعلق گیرد.';
