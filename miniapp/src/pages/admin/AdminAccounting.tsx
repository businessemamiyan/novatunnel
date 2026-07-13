import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { AccountingSummary, Expense, OtherRevenue, SalesStatsDetailed } from "../../types";

const EXPENSE_CATEGORIES = ["سرور", "برداشت شخصی", "تبلیغات", "سایر"];

export default function AdminAccounting() {
  const [sales, setSales] = useState<SalesStatsDetailed | null>(null);
  const [otherRevenue, setOtherRevenue] = useState<OtherRevenue | null>(null);
  const [summary, setSummary] = useState<AccountingSummary | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState(EXPENSE_CATEGORIES[0]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const load = () => {
    api.get<SalesStatsDetailed>("/accounting/sales-stats").then(setSales);
    api.get<OtherRevenue>("/accounting/other-revenue").then(setOtherRevenue);
    api.get<AccountingSummary>("/accounting/summary").then(setSummary);
    api.get<Expense[]>("/accounting/expenses").then(setExpenses);
  };
  useEffect(load, []);

  const addExpense = async () => {
    setError("");
    const amt = Number(amount);
    if (!amt || amt <= 0 || !description.trim()) {
      setError("مبلغ و توضیح را وارد کنید.");
      return;
    }
    try {
      await api.post<Expense>("/accounting/expenses", {
        amount_toman: amt,
        description: description.trim(),
        category,
      });
      setAmount("");
      setDescription("");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطا در ثبت هزینه");
    }
  };

  const removeExpense = async (id: string) => {
    await api.delete(`/accounting/expenses/${id}`);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">💼 حسابداری</p>

      {sales && (
        <div className="glass-card p-4 mb-3">
          <p className="text-sm font-medium mb-3">📊 شمارنده فروش</p>
          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              { label: "امروز", count: sales.today_count, amount: sales.today_sales },
              { label: "این هفته", count: sales.week_count, amount: sales.week_sales },
              { label: "این ماه", count: sales.month_count, amount: sales.month_sales },
            ].map((s) => (
              <div key={s.label}>
                <p className="text-[11px] m-0 mb-1" style={{ color: "var(--text-secondary)" }}>{s.label}</p>
                <p className="text-sm font-medium m-0" style={{ color: "var(--accent)" }}>
                  {s.count.toLocaleString("fa-IR")} فروش
                </p>
                <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>
                  {s.amount.toLocaleString("fa-IR")}ت
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {otherRevenue && (
        <div className="glass-card p-4 mb-3">
          <p className="text-sm font-medium mb-3">💳 سایر درآمدهای واقعی</p>
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            هزینه فعال‌سازی/ارتقای نمایندگان: {otherRevenue.agency_activation.total.toLocaleString("fa-IR")} تومان
          </p>
          <p className="text-xs m-0" style={{ color: "var(--text-secondary)" }}>
            شارژ کیف‌پول کاربران: {otherRevenue.wallet_topup.total.toLocaleString("fa-IR")} تومان
          </p>
        </div>
      )}

      {summary && (
        <div className="glass-card p-4 mb-4">
          <p className="text-sm font-medium mb-3">💰 سود / زیان</p>
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            فروش بسته‌ها: {summary.total_sales.toLocaleString("fa-IR")} تومان
          </p>
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            + فعال‌سازی نمایندگی: {summary.agency_activation_total.toLocaleString("fa-IR")} تومان
          </p>
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            + شارژ کیف‌پول: {summary.wallet_topup_total.toLocaleString("fa-IR")} تومان
          </p>
          <p className="text-xs m-0 mb-2" style={{ color: "var(--text-secondary)" }}>
            = مجموع درآمد {summary.total_revenue.toLocaleString("fa-IR")} − هزینه‌ها {summary.total_expenses.toLocaleString("fa-IR")}
          </p>
          <p
            className="text-lg font-medium m-0"
            style={{ color: summary.net_profit >= 0 ? "var(--accent)" : "var(--danger)" }}
          >
            سود خالص فعلی: {summary.net_profit.toLocaleString("fa-IR")} تومان
          </p>
        </div>
      )}

      <div className="glass-card p-4 mb-4">
        <p className="text-sm font-medium mb-3">➕ ثبت هزینه جدید</p>
        <label className="text-xs" style={{ color: "var(--text-secondary)" }}>مبلغ (تومان)</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
        />
        <label className="text-xs" style={{ color: "var(--text-secondary)" }}>توضیح</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="مثلاً: هزینه سرور هلند"
          className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
        />
        <label className="text-xs" style={{ color: "var(--text-secondary)" }}>دسته‌بندی</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
        >
          {EXPENSE_CATEGORIES.map((c) => (
            <option key={c} value={c} style={{ background: "var(--bg)" }}>{c}</option>
          ))}
        </select>
        {error && (
          <p className="text-[11px] mb-2" style={{ color: "var(--danger)" }}>
            {error}
          </p>
        )}
        <button
          onClick={addExpense}
          className="w-full text-sm px-4 py-2 rounded-full"
          style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
        >
          ثبت هزینه
        </button>
      </div>

      <p className="font-medium mb-2">تاریخچه هزینه‌ها</p>
      {expenses.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          هنوز هزینه‌ای ثبت نشده.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {expenses.map((e) => (
            <div key={e.id} className="glass-card p-3 flex items-center justify-between">
              <div>
                <p className="text-sm m-0 mb-1">{e.description}</p>
                <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>
                  {e.category && `${e.category} · `}
                  {new Date(e.created_at).toLocaleDateString("fa-IR")}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-sm" style={{ color: "var(--danger)" }}>
                  {e.amount_toman.toLocaleString("fa-IR")}ت
                </span>
                <button onClick={() => removeExpense(e.id)} className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  حذف
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
