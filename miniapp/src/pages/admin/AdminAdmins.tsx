import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { AdminEntry } from "../../types";

export default function AdminAdmins() {
  const [admins, setAdmins] = useState<AdminEntry[]>([]);
  const [newId, setNewId] = useState("");
  const navigate = useNavigate();

  const load = () => api.get<AdminEntry[]>("/admins").then(setAdmins);
  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    const id = Number(newId);
    if (!id) return;
    await api.post("/admins", { telegram_id: id });
    setNewId("");
    load();
  };

  const remove = async (id: number) => {
    if (!confirm(`دسترسی ادمین ${id} حذف شود؟`)) return;
    try {
      await api.delete(`/admins/${id}`);
      load();
    } catch (e) {
      alert("امکان حذف آخرین ادمین وجود ندارد.");
    }
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">👤 مدیریت ادمین‌ها</p>

      <div className="flex gap-2 mb-4">
        <input
          value={newId}
          onChange={(e) => setNewId(e.target.value)}
          placeholder="آیدی عددی تلگرام"
          className="flex-1 glass-card px-3 py-2 text-sm bg-transparent outline-none"
        />
        <button
          onClick={add}
          className="text-xs px-4 py-2 rounded-full"
          style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
        >
          ➕ افزودن
        </button>
      </div>

      <div className="flex flex-col gap-2">
        {admins.map((a) => (
          <div key={a.telegram_id} className="glass-card p-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium m-0">{a.telegram_id}</p>
              <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>
                {a.added_by ? `افزوده‌شده توسط ${a.added_by}` : "بنیان‌گذار"}
              </p>
            </div>
            <button
              onClick={() => remove(a.telegram_id)}
              className="text-xs px-3 py-1.5 rounded-full"
              style={{ background: "rgba(240,97,106,0.15)", color: "var(--danger)" }}
            >
              حذف
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
