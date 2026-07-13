import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";

export default function AdminBroadcast() {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ total: number; sent: number; failed: number } | null>(null);
  const navigate = useNavigate();

  const send = async () => {
    if (!text.trim()) return;
    if (!confirm(`این پیام برای همه کاربران ارسال شود؟`)) return;
    setSending(true);
    try {
      const res = await api.post<{ total: number; sent: number; failed: number }>("/broadcast", { text });
      setResult(res);
      setText("");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">📢 پیام همگانی</p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="متن پیام برای همه کاربران..."
        rows={6}
        className="w-full glass-card px-3 py-3 text-sm bg-transparent outline-none mb-3"
      />

      <button
        onClick={send}
        disabled={sending || !text.trim()}
        className="text-sm px-4 py-2.5 rounded-full w-full"
        style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
      >
        {sending ? "در حال ارسال..." : "📤 ارسال به همه"}
      </button>

      {result && (
        <div className="glass-card p-4 mt-4">
          <p className="text-sm m-0">کل: {result.total} · موفق: {result.sent} · ناموفق: {result.failed}</p>
        </div>
      )}
    </div>
  );
}
