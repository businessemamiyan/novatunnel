-- NovaTunnel — لایه اتوماسیون تبلیغات و فروش (خارج از سند قوانین اصلی)
-- تولید محتوا، پست خودکار تلگرام/اینستاگرام، و پاسخ‌گویی هوشمند با تشخیص نیاز به ادمین.

create table generated_posts (
  id uuid primary key default gen_random_uuid(),
  platform text not null check (platform in ('telegram', 'instagram')),
  content text not null,
  image_url text,
  status text not null default 'pending' check (status in ('pending', 'posted', 'failed')),
  external_post_id text,
  error_message text,
  created_at timestamptz not null default now(),
  posted_at timestamptz
);

comment on table generated_posts is 'تاریخچه پست‌های تبلیغاتی تولیدشده با Claude API و وضعیت انتشار هرکدام.';

create index idx_generated_posts_created_at on generated_posts(created_at desc);

create table social_conversation_log (
  id uuid primary key default gen_random_uuid(),
  platform text not null check (platform in ('telegram', 'instagram')),
  external_user_id text not null,
  external_username text,
  incoming_message text not null,
  action text not null check (action in ('replied', 'escalated')),
  reply_text text,
  escalation_reason text,
  created_at timestamptz not null default now()
);

comment on table social_conversation_log is 'هر پیام ورودی (DM/کامنت/چت تلگرام) که با Claude پردازش شده — یا پاسخ داده شده یا به ادمین ارجاع شده.';

create index idx_social_conversation_platform_user on social_conversation_log(platform, external_user_id);
create index idx_social_conversation_created_at on social_conversation_log(created_at desc);

create table instagram_handled_items (
  item_id text primary key,
  item_type text not null check (item_type in ('dm', 'comment')),
  handled_at timestamptz not null default now()
);

comment on table instagram_handled_items is 'جلوگیری از پاسخ تکراری به همان DM/کامنت هنگام poll دوره‌ای ماژول غیررسمی اینستاگرام.';

alter table generated_posts enable row level security;
alter table social_conversation_log enable row level security;
alter table instagram_handled_items enable row level security;
