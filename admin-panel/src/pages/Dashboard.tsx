import { useEffect, useState } from "react";
import { apiRequest, ApiError } from "../api";
import { usePageMeta } from "../layout/PageMetaContext";
import StatCard from "../components/StatCard";
import BarChart from "../components/BarChart";

interface DashboardData {
  accounts: { total: number; active: number; inactive: number };
  volume: { total_allocated_gb: number; total_used_gb: number };
  sales: { total_sales: number; today_sales: number; week_sales: number; month_sales: number };
  trend: { day: string; total: number; count: number }[];
  agents: { total: number; pending_activation_requests: number };
  pending_wallet_topups: number;
}

function toman(n: number) {
  return `${n.toLocaleString("fa-IR")} تومان`;
}

export default function Dashboard() {
  usePageMeta("داشبورد", "خلاصه‌ای از وضعیت فروش و مشتریان NovaTunnel");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<DashboardData>("/api/dashboard")
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "خطا در دریافت اطلاعات"));
  }, []);

  if (error) return <p className="badge danger">{error}</p>;
  if (!data) return <p className="text-[var(--text-secondary)]">در حال بارگذاری…</p>;

  return (
    <div className="flex flex-col gap-6">
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="کل کاربران" value={data.accounts.total.toLocaleString("fa-IR")} />
        <StatCard label="فروش امروز" value={toman(data.sales.today_sales)} />
        <StatCard label="فروش این هفته" value={toman(data.sales.week_sales)} />
        <StatCard label="فروش این ماه" value={toman(data.sales.month_sales)} />
      </section>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="سرویس‌های فعال" value={data.accounts.active.toLocaleString("fa-IR")} />
        <StatCard
          label="حجم مصرف‌شده"
          value={`${data.volume.total_used_gb.toFixed(1)} از ${data.volume.total_allocated_gb.toFixed(1)} گیگ`}
        />
        <StatCard label="نمایندگان فعال" value={data.agents.total.toLocaleString("fa-IR")} />
        <StatCard
          label="در انتظار تایید"
          value={(data.agents.pending_activation_requests + data.pending_wallet_topups).toLocaleString(
            "fa-IR",
          )}
          trend={data.agents.pending_activation_requests + data.pending_wallet_topups > 0 ? "نیاز به بررسی" : undefined}
          trendDown={data.agents.pending_activation_requests + data.pending_wallet_topups > 0}
        />
      </section>

      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-bold">روند فروش هفت روز اخیر</h2>
            <p className="text-xs text-[var(--text-secondary)]">مبلغ فروش تاییدشده به تومان</p>
          </div>
        </div>
        {data.trend.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">هنوز فروشی در این بازه ثبت نشده است.</p>
        ) : (
          <BarChart
            points={data.trend.map((t) => ({
              label: new Date(t.day).toLocaleDateString("fa-IR", { weekday: "short" }),
              value: t.total,
              title: `${toman(t.total)} · ${t.count} سفارش`,
            }))}
          />
        )}
      </section>
    </div>
  );
}
