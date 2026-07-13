-- NovaTunnel — کارت‌های اختصاصی نماینده + رفع باگ‌های گزارش‌شده کاربر
-- مرجع: NovaTunnel-Business-Rules.md بخش ۷ (سقف آزاد فروش نماینده) و بخش ۱۱ (حسابداری)

-- کارت‌های پرداخت حالا می‌توانند متعلق به یک نماینده مشخص باشند (NULL = کارت‌های مالک/ادمین).
-- مشتری‌ای که از طریق لینک اختصاصی نماینده خرید می‌کند باید مستقیماً به کارت خودِ نماینده پرداخت کند.
alter table payment_cards add column if not exists agent_id uuid references users(id) on delete cascade;
create index idx_payment_cards_agent_id on payment_cards(agent_id);
