-- NovaTunnel — پنل‌های VPN (Marzban / در حال مهاجرت از X-ui)
-- مرجع: NovaTunnel-Business-Rules.md بخش ۲، ۹

create table panels (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references users(id),
  marzban_username text unique,
  xui_client_id text,
  server_node text,
  protocol text not null default 'vless-reality',
  traffic_limit_gb numeric(12,3),
  traffic_used_gb numeric(12,3) not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on column panels.xui_client_id is 'بدهی معماری شناخته‌شده (بخش ۹ سند قوانین): مقدار marzban_username موقتاً در این ستون قدیمی ذخیره می‌شود تا فاز مهاجرت کامل از X-ui Sanaei به Marzban تمام شود.';

create index idx_panels_user_id on panels(user_id);

create trigger trg_panels_updated_at
before update on panels
for each row execute function set_updated_at();
