import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import { api } from "../api";
import { Me, ServiceSummary } from "../types";
import ServiceCard from "../components/ServiceCard";
import HeroGauge from "../components/HeroGauge";

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([api.get<Me>("/me"), api.get<ServiceSummary[]>("/my/services")])
      .then(([meData, servicesData]) => {
        setMe(meData);
        setServices(servicesData);
      })
      .finally(() => setLoading(false));
  }, []);

  const primary = services[0];
  const otherServices = services.slice(1);

  return (
    <div className="p-4 pb-24">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-4">
        <p className="text-lg font-medium m-0">
          درود{me?.first_name ? `، ${me.first_name}` : ""} 👋
        </p>
        <p className="text-sm m-0" style={{ color: "var(--text-secondary)" }}>
          به NovaTunnel خوش اومدی
        </p>
      </motion.div>

      {loading ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          در حال بارگذاری...
        </p>
      ) : primary ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card py-6 mb-5 flex flex-col items-center cursor-pointer"
          onClick={() => navigate(`/services/${primary.id}`)}
        >
          <HeroGauge
            remainingGb={Math.max(primary.traffic_limit_gb - primary.traffic_used_gb, 0)}
            totalGb={primary.traffic_limit_gb}
            label={primary.label}
          />
          <span
            className="mt-4 text-xs px-3 py-1 rounded-full"
            style={{ color: "var(--accent)", background: "rgba(62,232,195,0.12)" }}
          >
            {primary.status}
          </span>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-5 text-center"
        >
          <p className="text-2xl mb-2">👋</p>
          <p className="text-sm m-0 mb-4" style={{ color: "var(--text-secondary)" }}>
            هنوز سرویسی نداری — با یکی از این دو راه شروع کن
          </p>
          <div className="flex flex-col gap-2">
            <button
              onClick={() => navigate("/network")}
              className="text-sm px-4 py-2 rounded-full"
              style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
            >
              🎁 دعوت دوستان برای حجم رایگان
            </button>
            <button
              onClick={() => navigate("/purchase")}
              className="text-sm px-4 py-2 rounded-full"
              style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
            >
              🛒 خرید سرویس
            </button>
            <button
              onClick={() => navigate("/onboarding")}
              className="text-xs px-4 py-2"
              style={{ color: "var(--text-secondary)" }}
            >
              🚀 تازه‌واردی؟ آموزش تصویری رو ببین
            </button>
          </div>
        </motion.div>
      )}

      <div className="flex gap-3 mb-5">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 flex-1"
        >
          <p className="text-[11px] m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            🎁 حجم هدیه
          </p>
          <p className="text-lg font-medium m-0" style={{ color: "var(--accent)" }}>
            {(me?.gift_balance_gb ?? 0).toFixed(1)} گیگ
          </p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass-card p-4 flex-1 cursor-pointer"
          onClick={() => navigate("/wallet")}
        >
          <p className="text-[11px] m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            👛 کیف پول
          </p>
          <p className="text-lg font-medium m-0" style={{ color: "var(--accent-violet)" }}>
            {(me?.wallet_balance_toman ?? 0).toLocaleString("fa-IR")} ت
          </p>
        </motion.div>
      </div>

      {otherServices.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium m-0">دیگر سرویس‌های من</p>
            <button
              onClick={() => navigate("/services")}
              className="text-xs"
              style={{ color: "var(--accent)" }}
            >
              مشاهده همه ←
            </button>
          </div>
          <div className="flex flex-col gap-3">
            {otherServices.map((s, i) => (
              <ServiceCard key={s.id} service={s} index={i} onClick={() => navigate(`/services/${s.id}`)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
