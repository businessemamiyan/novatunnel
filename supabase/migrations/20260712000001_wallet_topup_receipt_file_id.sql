-- برای نمایش عکس رسید شارژ کیف‌پول در پنل ادمین (مشابه purchases.receipt_file_id)
alter table wallet_topup_requests add column if not exists receipt_file_id text;
