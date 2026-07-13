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
  const [status, setStatus] = useState<string>("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">🧩 مدیریت سرویس‌ها</p>

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
              <p className="font-medium m-0 mb-1">{p.label ?? p.marzban_username}</p>
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
