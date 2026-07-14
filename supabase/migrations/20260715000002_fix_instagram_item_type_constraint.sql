-- NovaTunnel — رفع باگ: item_type جدید «comment_dm_link» رد قانون قدیمی می‌شد
-- مرجع: SESSION-LOG.md بخش ۱۶ — این باگ باعث ارسال تکراری همون پیام دایرکت به یک کامنت‌گذار واقعی شد
-- و به احتمال زیاد باعث باطل شدن سشن اینستاگرام توسط خود پلتفرم شد.

alter table instagram_handled_items drop constraint instagram_handled_items_item_type_check;
alter table instagram_handled_items add constraint instagram_handled_items_item_type_check
  check (item_type in ('dm', 'comment', 'comment_dm_link'));
