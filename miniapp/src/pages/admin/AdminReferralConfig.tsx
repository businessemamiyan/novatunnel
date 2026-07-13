import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";

interface ReferralLevel {
  level: number;
  max_direct_children: number;
  reward_percent: number;
  monthly_cap_gb: number;
}

interface Edits {
  max_direct_children?: string;
  reward_percent?: string;
  monthly_cap_gb?: string;
}

const LEVEL_LABELS: Record<number, string> = {
  1: "سطح ۱ (زیرمجموعه مستقیم)",
  2: "سطح ۲",
  3: "سطح ۳",
};

export default function AdminReferralConfig() {
  const [levels, setLevels] = useState<ReferralLevel[]>([]);
  const [edits, setEdits] = useState<Record<number, Edits>>({});
  const [savedLevel, setSavedLevel] = useState<number | null>(null);
  const navigate = useNavigate();

  const load = () => api.get<ReferralLevel[]>("/referral-config").then(setLevels);
  useEffect(() => {
    load();
  }, []);

  const setField = (level: number, field: keyof Edits, value: string) => {
    setEdits((prev) => ({ ...prev, [level]: { ...prev[level], [field]: value } }));
  };

  const save = async (l: ReferralLevel) => {
    const e = edits[l.level] || {};
    const max_direct_children = Number(e.max_direct_children ?? l.max_direct_children);
    const reward_percent = Number(e.reward_percent ?? l.reward_percent);
    const monthly_cap_gb = Number(e.monthly_cap_gb ?? l.monthly_cap_gb);
    if (!max_direct_children || reward_percent <= 0 || !monthly_cap_gb) return;

    await api.patch(`/referral-config/${l.level}`, { max_direct_children, reward_percent, monthly_cap_gb });
    setSavedLevel(l.level);
    setTimeout(() => setSavedLevel(null), 1200);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">🎯 سیستم چندسطحی مشتری عادی</p>
      <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
        فقط حداکثر زیرمجموعه مستقیم سطح ۱ واقعاً enforce می‌شود؛ اعداد سطح ۲ و ۳ صرفاً مرجع محاسباتی‌اند.
      </p>

      <div className="flex flex-col gap-3">
        {levels.map((l) => (
          <div key={l.level} className="glass-card p-4">
            <p className="font-medium m-0 mb-3">{LEVEL_LABELS[l.level] || `سطح ${l.level}`}</p>

            <div className="flex flex-col gap-2 mb-3">
              {l.level === 1 && (
                <>
                  <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    حداکثر زیرمجموعه مستقیم
                  </label>
                  <input
                    type="number"
                    defaultValue={l.max_direct_children}
                    onChange={(e) => setField(l.level, "max_direct_children", e.target.value)}
                    className="glass-card px-3 py-2 text-sm bg-transparent outline-none"
                  />
                </>
              )}

              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                درصد پاداش حجم هدیه
              </label>
              <input
                type="number"
                step="0.1"
                defaultValue={l.reward_percent}
                onChange={(e) => setField(l.level, "reward_percent", e.target.value)}
                className="glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />

              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                سقف ماهانه این سطح (گیگ)
              </label>
              <input
                type="number"
                defaultValue={l.monthly_cap_gb}
                onChange={(e) => setField(l.level, "monthly_cap_gb", e.target.value)}
                className="glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />
            </div>

            <button
              onClick={() => save(l)}
              className="text-xs px-4 py-2 rounded-full"
              style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
            >
              {savedLevel === l.level ? "ذخیره شد ✅" : "ذخیره"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
