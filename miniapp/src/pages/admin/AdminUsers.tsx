import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, downloadFile } from "../../api";

interface UserRow {
  id: string;
  telegram_id: number;
  telegram_username: string | null;
  full_name: string | null;
  phone_number: string | null;
  phone_verified: boolean;
  wallet_balance_toman: number;
  gift_balance_gb: number;
  last_purchase_at: string | null;
  created_at: string;
}

export default function AdminUsers() {
  const [items, setItems] = useState<UserRow[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [grantingId, setGrantingId] = useState<string | null>(null);
  const [grantAmount, setGrantAmount] = useState("");
  const [grantStatus, setGrantStatus] = useState<Record<string, string>>({});
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    api
      .get<{ total: number; items: UserRow[] }>(`/users?search=${encodeURIComponent(search)}&limit=50`)
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const exportExcel = async () => {
    setExporting(true);
    try {
      await downloadFile("/users/export", "novatunnel_users.xlsx");
    } finally {
      setExporting(false);
    }
  };

  const submitGrant = async (userId: string) => {
    const amount = Number(grantAmount);
    if (!amount || amount <= 0) return;
    try {
      await api.post(`/users/${userId}/grant-gift`, { amount_gb: amount });
      setGrantStatus((prev) => ({ ...prev, [userId]: `✅ ${amount} گیگ اعطا شد` }));
      setGrantingId(null);
      setGrantAmount("");
      load();
    } catch (e) {
      setGrantStatus((prev) => ({
        ...prev,
        [userId]: e instanceof Error ? e.message : "خطا در اعطای حجم",
      }));
    }
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>

      <div className="flex items-center justify-between mb-4">
        <p className="text-lg font-medium m-0">👥 کاربران ({total})</p>
        <button
          onClick={exportExcel}
          disabled={exporting}
          className="text-xs px-3 py-1.5 rounded-full"
          style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
        >
          {exporting ? "در حال آماده‌سازی..." : "📊 خروجی اکسل"}
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="جستجو با نام، یوزرنیم یا شماره..."
          className="flex-1 glass-card px-3 py-2 text-sm bg-transparent outline-none"
        />
        <button
          onClick={load}
          className="text-xs px-4 py-2 rounded-full"
          style={{ background: "var(--surface)", color: "var(--text-secondary)", border: "1px solid var(--surface-border)" }}
        >
          جستجو
        </button>
      </div>

      {loading ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          در حال بارگذاری...
        </p>
      ) : items.length === 0 ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          کاربری پیدا نشد.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {items.map((u) => (
            <div key={u.id} className="glass-card p-3">
              <p className="text-sm font-medium m-0 mb-1">
                {u.full_name || "-"} {u.telegram_username && `(@${u.telegram_username})`}
              </p>
              <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
                📱 {u.phone_number || "احراز نشده"} {u.phone_verified && "✅"}
              </p>
              <p className="text-xs m-0 mb-2" style={{ color: "var(--text-secondary)" }}>
                👛 {u.wallet_balance_toman.toLocaleString("fa-IR")} ت · 🎁 {u.gift_balance_gb.toFixed(1)} گیگ ·{" "}
                {new Date(u.created_at).toLocaleDateString("fa-IR")}
              </p>

              {grantingId === u.id ? (
                <div className="flex gap-2 items-center">
                  <input
                    type="number"
                    value={grantAmount}
                    onChange={(e) => setGrantAmount(e.target.value)}
                    placeholder="مقدار گیگ"
                    className="flex-1 glass-card px-2 py-1 text-xs bg-transparent outline-none"
                  />
                  <button
                    onClick={() => submitGrant(u.id)}
                    className="text-xs px-3 py-1.5 rounded-full"
                    style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
                  >
                    ثبت
                  </button>
                  <button
                    onClick={() => { setGrantingId(null); setGrantAmount(""); }}
                    className="text-xs px-3 py-1.5 rounded-full"
                    style={{ background: "var(--surface)", color: "var(--text-secondary)" }}
                  >
                    انصراف
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => { setGrantingId(u.id); setGrantAmount(""); }}
                  className="text-xs px-3 py-1.5 rounded-full"
                  style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
                >
                  🎁 اعطای حجم هدیه
                </button>
              )}
              {grantStatus[u.id] && (
                <p className="text-[11px] mt-1 m-0" style={{ color: "var(--text-secondary)" }}>
                  {grantStatus[u.id]}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
