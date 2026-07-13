import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { ActivityLogEntry } from "../../types";

const ACTION_LABELS: Record<string, string> = {
  receipt_approve: "✅ تایید رسید",
  receipt_reject: "❌ رد رسید",
  service_delete: "🗑 حذف سرویس",
  service_renew: "🔁 تمدید سرویس",
  package_price_update: "💰 تغییر قیمت",
  broadcast_sent: "📢 پیام همگانی",
  admin_add: "➕ افزودن ادمین",
  admin_remove: "➖ حذف ادمین",
};

export default function AdminActivityLog() {
  const [items, setItems] = useState<ActivityLogEntry[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get<ActivityLogEntry[]>("/activity-log").then(setItems);
  }, []);

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">📜 لاگ فعالیت ادمین‌ها</p>

      <div className="flex flex-col gap-2">
        {items.map((entry) => (
          <div key={entry.id} className="glass-card p-3">
            <p className="text-sm font-medium m-0">
              {ACTION_LABELS[entry.action_type] ?? entry.action_type}
            </p>
            {entry.target_description && (
              <p className="text-xs m-0" style={{ color: "var(--text-secondary)" }}>
                {entry.target_description}
              </p>
            )}
            <p className="text-[11px] m-0 mt-1" style={{ color: "var(--text-secondary)" }}>
              ادمین {entry.admin_telegram_id} · {new Date(entry.created_at).toLocaleString("fa-IR")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
