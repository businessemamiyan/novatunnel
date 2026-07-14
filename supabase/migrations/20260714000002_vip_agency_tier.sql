-- NovaTunnel — رده نمایندگی «ویژه» (دسترسی نماینده به فروش سرویس مقاوم/رله ایران)
-- مرجع: NovaTunnel-Business-Rules.md بخش ۶، SESSION-LOG.md بخش ۱۴

alter type agency_tier add value if not exists 'vip';

insert into agency_tier_config (tier, activation_fee_toman, purchase_rate_toman_per_gb, min_wallet_balance_toman)
values ('vip', 5000000, 6000, 200000)
on conflict (tier) do nothing;

comment on column agency_tier_config.tier is 'silver/gold/diamond: رده‌های معمولی بر اساس حجم؛ vip: رده ارتقایی که علاوه بر فروش معمولی، امکان فروش سرویس ویژه (مقاوم در برابر فیلترینگ، از طریق رله ایران) را هم می‌دهد — نرخ خرید بالاتر (بخش ۶.۱ سند) چون زیرساخت اختصاصی مصرف می‌کند.';

-- برای فروش دستی نماینده (که package_id ندارد) — امکان علامت‌زدن یک فروش به‌عنوان سرویس ویژه
alter table purchases add column if not exists is_vip_service boolean not null default false;

comment on column purchases.is_vip_service is 'true یعنی سرویس ساخته‌شده باید اینباند VLESS TCP REALITY VIP هم داشته باشد — یا از بسته is_vip=true آمده، یا نماینده صریحاً هنگام فروش دستی علامت زده (بخش ۱۴ گزارش جلسه).';
