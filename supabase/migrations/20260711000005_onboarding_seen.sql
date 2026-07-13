-- برای نمایش خودکار آموزش تصویری فقط یک‌بار، در اولین ورود کاربر جدید به Mini App
alter table users add column if not exists onboarding_seen boolean not null default false;

-- کاربرهای موجود قبل از این migration را «قبلاً دیده» علامت بزن تا با اولین ورودشان بعد از این تغییر، آموزش برایشان باز نشود
update users set onboarding_seen = true where onboarding_seen = false;
