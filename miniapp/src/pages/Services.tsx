import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import { ServiceSummary } from "../types";
import ServiceCard from "../components/ServiceCard";

export default function Services() {
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get<ServiceSummary[]>("/my/services")
      .then(setServices)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 pb-24">
      <p className="text-lg font-medium mb-4">🧩 سرویس‌های من</p>

      {loading ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          در حال بارگذاری...
        </p>
      ) : services.length === 0 ? (
        <div className="glass-card p-6 text-center">
          <p className="text-2xl mb-2">🧩</p>
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
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {services.map((s, i) => (
            <ServiceCard key={s.id} service={s} index={i} onClick={() => navigate(`/services/${s.id}`)} />
          ))}
        </div>
      )}
    </div>
  );
}
