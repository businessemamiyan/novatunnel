import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { AgencyTierConfig } from "../../types";

const TIER_LABELS: Record<string, string> = {
  silver: "🥈 نقره‌ای",
  gold: "🥇 طلایی",
  diamond: "💎 برلیان",
};

interface Edits {
  activation_fee_toman?: string;
  purchase_rate_toman_per_gb?: string;
  min_wallet_balance_toman?: string;
}

export default function AdminAgencyTiers() {
  const [tiers, setTiers] = useState<AgencyTierConfig[]>([]);
  const [edits, setEdits] = useState<Record<string, Edits>>({});
  const [savedTier, setSavedTier] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = () => api.get<AgencyTierConfig[]>("/agency-config").then(setTiers);
  useEffect(() => {
    load();
  }, []);

  const setField = (tier: string, field: keyof Edits, value: string) => {
    setEdits((prev) => ({ ...prev, [tier]: { ...prev[tier], [field]: value } }));
  };

  const save = async (t: AgencyTierConfig) => {
    const e = edits[t.tier] || {};
    const activation_fee_toman = Number(e.activation_fee_toman ?? t.activation_fee_toman);
    const purchase_rate_toman_per_gb = Number(e.purchase_rate_toman_per_gb ?? t.purchase_rate_toman_per_gb);
    const min_wallet_balance_toman = Number(e.min_wallet_balance_toman ?? t.min_wallet_balance_toman);
    if (!activation_fee_toman || !purchase_rate_toman_per_gb || !min_wallet_balance_toman) return;

    await api.patch(`/agency-config/${t.tier}`, {
      activation_fee_toman,
      purchase_rate_toman_per_gb,
      min_wallet_balance_toman,
    });
    setSavedTier(t.tier);
    setTimeout(() => setSavedTier(null), 1200);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">🏷 قیمت‌گذاری رده‌های نمایندگی</p>

      <div className="flex flex-col gap-3">
        {tiers.map((t) => (
          <div key={t.tier} className="glass-card p-4">
            <p className="font-medium m-0 mb-3">{TIER_LABELS[t.tier] || t.tier}</p>

            <div className="flex flex-col gap-2 mb-3">
              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                هزینه فعال‌سازی (تومان)
              </label>
              <input
                type="number"
                defaultValue={t.activation_fee_toman}
                onChange={(e) => setField(t.tier, "activation_fee_toman", e.target.value)}
                className="glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />

              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                نرخ خرید هر گیگ (تومان)
              </label>
              <input
                type="number"
                defaultValue={t.purchase_rate_toman_per_gb}
                onChange={(e) => setField(t.tier, "purchase_rate_toman_per_gb", e.target.value)}
                className="glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />

              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                حداقل موجودی کیف‌پول برای فعال ماندن (تومان)
              </label>
              <input
                type="number"
                defaultValue={t.min_wallet_balance_toman}
                onChange={(e) => setField(t.tier, "min_wallet_balance_toman", e.target.value)}
                className="glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />
            </div>

            <button
              onClick={() => save(t)}
              className="text-xs px-4 py-2 rounded-full"
              style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
            >
              {savedTier === t.tier ? "ذخیره شد ✅" : "ذخیره"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
