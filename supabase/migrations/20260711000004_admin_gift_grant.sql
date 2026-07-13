-- امکان اعطای دستی حجم هدیه توسط ادمین به یک کاربر انتخابی (بخش مدیریت پاداش‌ها)
alter type gift_ledger_entry_type add value if not exists 'admin_grant';
