-- اعتبار پاداش: تبدیل حجم هدیه انباشته به یک موجودی ریالی جداگانه که فقط صرف خرید بسته حجم می‌شود
-- (غیرقابل برداشت، غیرقابل انتقال) — با خرید پنل کلید فعال/تبدیل می‌شود. نرخ تبدیل: ۵۰۰۰ تومان/گیگ.
alter table users add column if not exists reward_credit_toman numeric not null default 0;

alter table purchases add column if not exists reward_credit_used_toman numeric not null default 0;
