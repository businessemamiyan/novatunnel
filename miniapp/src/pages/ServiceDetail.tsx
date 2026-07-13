import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";

import { api, fetchQrImage } from "../api";
import { ServiceDetail as ServiceDetailType } from "../types";
import HeroGauge from "../components/HeroGauge";

export default function ServiceDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [service, setService] = useState<ServiceDetailType | null>(null);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = () => {
    if (!id) return;
    api.get<ServiceDetailType>(`/my/services/${id}`).then(setService);
    fetchQrImage(id).then(setQrUrl).catch(() => {});
  };

  useEffect(load, [id]);

  const toggleActive = async () => {
    if (!id) return;
    setBusy(true);
    try {
      await api.post(`/my/services/${id}/toggle`);
      load();
    } finally {
      setBusy(false);
    }
  };

  const regenerateLink = async () => {
    if (!id) return;
    if (!confirm("لینک اشتراک قبلی باطل می‌شود و لینک جدید صادر می‌شود. ادامه می‌دهید؟")) return;
    setBusy(true);
    try {
      await api.post(`/my/services/${id}/regenerate-link`);
      load();
    } finally {
      setBusy(false);
    }
  };

  if (!service) {
    return (
      <div className="p-4 pb-24">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          در حال بارگذاری...
        </p>
      </div>
    );
  }

  const remaining = Math.max(service.traffic_limit_gb - service.traffic_used_gb, 0);

  const copyLink = async () => {
    if (!service.subscription_url) return;
    await navigator.clipboard.writeText(service.subscription_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card py-6 mb-4 flex flex-col items-center"
      >
        <HeroGauge remainingGb={remaining} totalGb={service.traffic_limit_gb} label={service.label} />
        <span
          className="mt-3 text-xs px-3 py-1 rounded-full"
          style={{ color: "var(--accent)", background: "rgba(62,232,195,0.12)" }}
        >
          {service.status}
        </span>

        {service.expires_at && (
          <p className="text-xs mt-3" style={{ color: "var(--text-secondary)" }}>
            انقضا: {new Date(service.expires_at).toLocaleDateString("fa-IR")}
          </p>
        )}
      </motion.div>

      {qrUrl && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-5 mb-4 flex flex-col items-center"
        >
          <img src={qrUrl} alt="QR اتصال" className="w-56 h-56 rounded-xl" />
          <button
            onClick={copyLink}
            className="mt-4 text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
          >
            {copied ? "کپی شد ✅" : "📋 کپی لینک اشتراک"}
          </button>
        </motion.div>
      )}

      <div className="flex flex-col gap-2">
        <button
          onClick={() => navigate(`/purchase?renew=${id}`)}
          disabled={busy}
          className="text-sm px-4 py-2 rounded-full"
          style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
        >
          🔁 تمدید سرویس
        </button>
        <button
          onClick={regenerateLink}
          disabled={busy}
          className="text-sm px-4 py-2 rounded-full"
          style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
        >
          🔗 تغییر لینک اشتراک
        </button>
        <button
          onClick={toggleActive}
          disabled={busy}
          className="text-sm px-4 py-2 rounded-full"
          style={{ background: "rgba(240,97,106,0.12)", color: "var(--danger)" }}
        >
          ⏸️ فعال/غیرفعال کردن سرویس
        </button>
      </div>
    </div>
  );
}
