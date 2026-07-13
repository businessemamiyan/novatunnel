-- برای جلوگیری از تکرار موضوع/بسته یکسان در پست‌های خودکار پی‌درپی
alter table generated_posts add column if not exists topic text;
