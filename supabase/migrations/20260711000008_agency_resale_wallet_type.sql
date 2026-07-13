-- هزینه‌ای که از کیف‌پول نماینده هنگام فروش حجم به مشتری خودش کسر می‌شود (بخش ۶.۴)
alter type wallet_tx_type add value if not exists 'agency_resale_cost';
