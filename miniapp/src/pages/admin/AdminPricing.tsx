import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { Package } from "../../types";

export default function AdminPricing() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [edits, setEdits] = useState<Record<number, string>>({});
  const [badgeEdits, setBadgeEdits] = useState<Record<number, string>>({});
  const [savedId, setSavedId] = useState<number | null>(null);
  const navigate = useNavigate();

  const load = () => api.get<Package[]>("/packages").then(setPackages);
  useEffect(() => {
    load();
  }, []);

  const save = async (id: number) => {
    const value = Number(edits[id]);
    if (!value) return;
    await api.patch(`/packages/${id}`, { retail_price_toman: value });
    setSavedId(id);
    setTimeout(() => setSavedId(null), 1200);
    load();
  };

  const saveBadge = async (id: number) => {
    const badge = (badgeEdits[id] ?? "").trim();
    await api.patch(`/packages/${id}/badge`, { badge: badge || null });
    setSavedId(id);
    setTimeout(() => setSavedId(null), 1200);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">💰 قیمت‌گذاری بسته‌ها</p>

      <div className="flex flex-col gap-3">
        {packages.map((p) => (
          <div key={p.id} className="glass-card p-4">
            <p className="font-medium m-0 mb-1">
              {p.name} {p.badge && <span style={{ color: "var(--accent-violet)" }}>· {p.badge}</span>}
            </p>
            <p className="text-xs m-0 mb-3" style={{ color: "var(--text-secondary)" }}>
              {p.volume_gb} گیگ · فعلی: {p.retail_price_toman.toLocaleString("fa-IR")} تومان
            </p>
            <div className="flex gap-2 mb-2">
              <input
                type="number"
                placeholder="قیمت جدید (تومان)"
                defaultValue={p.retail_price_toman}
                onChange={(e) => setEdits((prev) => ({ ...prev, [p.id]: e.target.value }))}
                className="flex-1 glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />
              <button
                onClick={() => save(p.id)}
                className="text-xs px-4 py-2 rounded-full"
                style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
              >
                {savedId === p.id ? "ذخیره شد ✅" : "ذخیره"}
              </button>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="برچسب (مثلاً اقتصادی، محبوب، پرمصرف)"
                defaultValue={p.badge ?? ""}
                onChange={(e) => setBadgeEdits((prev) => ({ ...prev, [p.id]: e.target.value }))}
                className="flex-1 glass-card px-3 py-2 text-sm bg-transparent outline-none"
              />
              <button
                onClick={() => saveBadge(p.id)}
                className="text-xs px-4 py-2 rounded-full"
                style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
              >
                ذخیره برچسب
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
