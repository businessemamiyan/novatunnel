import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";

interface AgencyRequest {
  id: string;
  tier: string;
  activation_fee_toman: number;
  is_upgrade: boolean;
  status: string;
  created_at: string;
  telegram_id: number;
  telegram_username: string | null;
  full_name: string | null;
}

const TIER_LABELS: Record<string, string> = {
  silver: "🥈 نقره‌ای",
  gold: "🥇 طلایی",
  diamond: "💎 برلیان",
};

const TABS: { key: string; label: string }[] = [
  { key: "pending", label: "در انتظار" },
  { key: "confirmed", label: "تایید‌شده" },
  { key: "rejected", label: "رد‌شده" },
];

export default function AdminAgencyRequests() {
  const [tab, setTab] = useState("pending");
  const [items, setItems] = useState<AgencyRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    api
      .get<AgencyRequest[]>(`/agency/admin/requests?status=${tab}`)
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(load, [tab]);

  const approve = async (id: string) => {
    await api.post(`/agency/admin/requests/${id}/approve`);
    load();
  };
  const reject = async (id: string) => {
    if (!confirm("این درخواست رد شود؟")) return;
    await api.post(`/agency/admin/requests/${id}/reject`);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">🏷 درخواست‌های نمایندگی</p>

      <div className="flex gap-2 mb-4">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="text-xs px-3 py-1.5 rounded-full"
            style={{
              background: tab === t.key ? "rgba(62,232,195,0.2)" : "transparent",
              color: tab === t.key ? "var(--accent)" : "var(--text-secondary)",
              border: "1px solid var(--surface-border)",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>در حال بارگذاری...</p>
      ) : items.length === 0 ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>درخواستی در این وضعیت نیست.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((r) => (
            <div key={r.id} className="glass-card p-4">
              <p className="font-medium m-0 mb-1">
                {r.full_name} (@{r.telegram_username ?? "-"})
              </p>
              <p className="text-xs m-0 mb-3" style={{ color: "var(--text-secondary)" }}>
                {TIER_LABELS[r.tier] || r.tier} {r.is_upgrade && "(ارتقا)"} ·{" "}
                {r.activation_fee_toman.toLocaleString("fa-IR")} تومان ·{" "}
                {new Date(r.created_at).toLocaleString("fa-IR")}
              </p>
              {tab === "pending" && (
                <div className="flex gap-2">
                  <button
                    onClick={() => approve(r.id)}
                    className="text-xs px-3 py-1.5 rounded-full"
                    style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
                  >
                    ✅ تایید
                  </button>
                  <button
                    onClick={() => reject(r.id)}
                    className="text-xs px-3 py-1.5 rounded-full"
                    style={{ background: "rgba(240,97,106,0.15)", color: "var(--danger)" }}
                  >
                    ❌ رد
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
