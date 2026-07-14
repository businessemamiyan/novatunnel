import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";

interface AdminPanel {
  id: string;
  label: string | null;
  marzban_username: string;
  telegram_username: string | null;
  full_name: string | null;
  traffic_limit_gb: number;
  traffic_used_gb: number;
  expires_at: string | null;
  is_active: boolean;
}

export default function AdminServices() {
  const [items, setItems] = useState<AdminPanel[]>([]);
  const [status, setStatus] = useState<string>("active");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const [grantTelegramId, setGrantTelegramId] = useState("");
  const [grantVolumeGb, setGrantVolumeGb] = useState("");
  const [grantLabel, setGrantLabel] = useState("");
  const [grantVip, setGrantVip] = useState(false);
  const [grantResult, setGrantResult] = useState("");
  const [grantError, setGrantError] = useState("");
  const [showGrantForm, setShowGrantForm] = useState(false);

  const load = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (search) params.set("search", search);
    api
      .get<AdminPanel[]>(`/services?${params.toString()}`)
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(load, [status]);

  const del = async (id: string) => {
    if (!confirm("این سرویس کاملاً حذف شود؟")) return;
    await api.delete(`/services/${id}`);
    load();
  };

  const renew = async (id: string) => {
    const gb = prompt("چند گیگ اضافه شود؟", "30");
    if (!gb) return;
    const days = prompt("چند روز تمدید شود؟", "30");
    await api.post(`/services/${id}/renew`, {
      add_volume_gb: Number(gb),
      extend_days: Number(days ?? 30),
    });
    load();
  };

  const grantService = async () => {
    setGrantError("");
    setGrantResult("");
    const vol = Number(grantVolumeGb);
    if (!grantTelegramId || !vol) {
      setGrantError("آیدی عددی تلگرام و حجم را وارد کنید.");
      return;
    }
    try {
      const res = await api.post<{ id: string; panel_status: string }>("/services/grant", {
        telegram_id: Number(grantTelegramId),
        volume_gb: vol,
        service_label: grantLabel || undefined,
        is_vip_service: grantVip,
      });
      setGrantResult(res.panel_status);
      setGrantTelegramId("");
      setGrantVolumeGb("");
      setGrantLabel("");
      setGrantVip(false);
      load();
    } catch (e) {
      setGrantError(e instanceof Error ? e.message : "خطا در ثبت سرویس تست");
    }
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">🧩 مدیریت سرویس‌ها</p>

      <button
        onClick={() => setShowGrantForm((v) => !v)}
        className="w-full text-sm px-4 py-2 rounded-full mb-4"
        style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
      >
        🎁 اعطای سرویس تست/رایگان (در حسابداری حساب نمی‌شود)
      </button>

      {showGrantForm && (
        <div className="glass-card p-4 mb-4">
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>آیدی عددی تلگرام کاربر</label>
          <input
            type="number"
            value={grantTelegramId}
            onChange={(e) => setGrantTelegramId(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
            dir="ltr"
          />
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>حجم (گیگ)</label>
          <input
            type="number"
            value={grantVolumeGb}
            onChange={(e) => setGrantVolumeGb(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          />
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>اسم دلخواه سرویس (اختیاری)</label>
          <input
            type="text"
            value={grantLabel}
            onChange={(e) => setGrantLabel(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          />
          <label className="flex items-center gap-2 text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            <input type="checkbox" checked={grantVip} onChange={(e) => setGrantVip(e.target.checked)} />
            🛡 این سرویس ویژه باشد (مسیر مقاوم فیلترینگ)
          </label>
          {grantError && <p className="text-[11px] mb-2" style={{ color: "var(--danger)" }}>{grantError}</p>}
          {grantResult && <p className="text-[11px] mb-2" style={{ color: "var(--accent)" }}>{grantResult}</p>}
          <button
            onClick={grantService}
            className="w-full text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
          >
            ثبت و تحویل سرویس
          </button>
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="جستجو (یوزرنیم، اسم سرویس)"
          className="flex-1 glass-card px-3 py-2 text-sm bg-transparent outline-none"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="glass-card px-2 py-2 text-sm bg-transparent"
        >
          <option value="">همه</option>
          <option value="active">فعال</option>
          <option value="inactive">غیرفعال</option>
        </select>
      </div>

      {loading ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>در حال بارگذاری...</p>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((p) => (
            <div key={p.id} className="glass-card p-4">
              <div className="flex items-center justify-between mb-1">
                <p className="font-medium m-0">{p.label ?? p.marzban_username}</p>
                <span
                  className="text-[11px] px-2 py-1 rounded-full shrink-0"
                  style={{
                    background: p.is_active ? "rgba(62,232,195,0.15)" : "rgba(240,97,106,0.15)",
                    color: p.is_active ? "var(--accent)" : "var(--danger)",
                  }}
                >
                  {p.is_active ? "فعال" : "❌ حذف‌شده"}
                </span>
              </div>
              <p className="text-xs m-0 mb-2" style={{ color: "var(--text-secondary)" }}>
                @{p.telegram_username ?? "بدون‌یوزرنیم"} · {p.full_name}
              </p>
              <p className="text-xs m-0 mb-3" style={{ color: "var(--text-secondary)" }}>
                {p.traffic_used_gb.toFixed(1)} / {p.traffic_limit_gb.toFixed(1)} گیگ ·{" "}
                {p.expires_at ? new Date(p.expires_at).toLocaleDateString("fa-IR") : "بدون انقضا"}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => renew(p.id)}
                  className="text-xs px-3 py-1.5 rounded-full"
                  style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
                >
                  🔁 تمدید
                </button>
                <button
                  onClick={() => del(p.id)}
                  className="text-xs px-3 py-1.5 rounded-full"
                  style={{ background: "rgba(240,97,106,0.15)", color: "var(--danger)" }}
                >
                  🗑 حذف
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
