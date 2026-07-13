import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import { api } from "../../api";
import { Stats } from "../../types";
import StatCard from "../../components/StatCard";
import BarChart from "../../components/BarChart";

const sections = [
  { path: "/admin/accounting", icon: "💼", label: "حسابداری" },
  { path: "/admin/services", icon: "🧩", label: "مدیریت سرویس‌ها" },
  { path: "/admin/receipts", icon: "🧾", label: "رسیدهای پرداخت" },
  { path: "/admin/wallet-topups", icon: "👛", label: "شارژ کیف‌پول" },
  { path: "/admin/pricing", icon: "💰", label: "قیمت‌گذاری" },
  { path: "/admin/payment-cards", icon: "💳", label: "شماره کارت‌ها" },
  { path: "/admin/agency-tiers", icon: "🏷", label: "رده‌های نمایندگی" },
  { path: "/admin/agency-requests", icon: "📥", label: "درخواست‌های نمایندگی" },
  { path: "/admin/referral-config", icon: "🎯", label: "سیستم چندسطحی" },
  { path: "/admin/users", icon: "👥", label: "کاربران" },
  { path: "/admin/broadcast", icon: "📢", label: "پیام همگانی" },
  { path: "/admin/admins", icon: "👤", label: "ادمین‌ها" },
  { path: "/admin/activity", icon: "📜", label: "لاگ فعالیت" },
];

export default function AdminHome() {
  const [stats, setStats] = useState<Stats | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get<Stats>("/stats").then(setStats);
  }, []);

  return (
    <div className="p-4 pb-24">
      <p className="text-lg font-medium mb-4">🛠 پنل مدیریت</p>

      {stats && (
        <>
          <div className="flex gap-3 mb-3 flex-wrap">
            <StatCard label="کل اکانت‌ها" value={String(stats.accounts.total)} />
            <StatCard label="فعال" value={String(stats.accounts.active)} accent="violet" />
          </div>
          <div className="flex gap-3 mb-3 flex-wrap">
            <StatCard label="حجم تخصیص‌داده" value={`${stats.volume.total_allocated_gb.toFixed(0)} گیگ`} />
            <StatCard label="حجم مصرف‌شده" value={`${stats.volume.total_used_gb.toFixed(0)} گیگ`} accent="violet" />
          </div>
          <div className="flex gap-3 mb-4 flex-wrap">
            <StatCard label="فروش امروز" value={`${stats.sales.today_sales.toLocaleString("fa-IR")} ت`} />
            <StatCard label="فروش این ماه" value={`${stats.sales.month_sales.toLocaleString("fa-IR")} ت`} accent="violet" />
          </div>

          <div className="glass-card p-4 mb-5">
            <p className="text-sm font-medium mb-3">📈 روند فروش ۷ روز اخیر</p>
            <BarChart
              data={stats.trend.map((t) => ({
                label: t.day.slice(5),
                value: t.total,
              }))}
            />
          </div>
        </>
      )}

      <div className="grid grid-cols-2 gap-3">
        {sections.map((s, i) => (
          <motion.button
            key={s.path}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate(s.path)}
            className="glass-card p-4 flex flex-col items-center gap-2"
          >
            <span className="text-2xl">{s.icon}</span>
            <span className="text-xs">{s.label}</span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
