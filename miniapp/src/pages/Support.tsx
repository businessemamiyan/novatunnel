import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import { openExternalLink } from "../telegram";

const INSTAGRAM_URL = "https://www.instagram.com/nova_tunnel";

const TOPICS = [
  { value: "payment", label: "💳 مشکل پرداخت" },
  { value: "connection", label: "🌐 مشکل اتصال" },
  { value: "general", label: "❓ سوال عمومی" },
  { value: "agency", label: "🤝 درخواست نمایندگی" },
];

export default function Support() {
  const [topic, setTopic] = useState<string>("general");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const navigate = useNavigate();

  const send = async () => {
    if (!message.trim()) return;
    setSending(true);
    try {
      await api.post("/support", { message: message.trim(), topic });
      setSent(true);
      setMessage("");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="p-4 pb-24">
      <p className="text-lg font-medium mb-4">🎫 تماس با پشتیبانی</p>

      <div className="glass-card p-4 mb-4">
        {sent ? (
          <p className="text-sm text-center py-4" style={{ color: "var(--accent)" }}>
            ✅ پیام شما ارسال شد. به‌زودی پاسخ داده می‌شود.
          </p>
        ) : (
          <>
            <p className="text-xs mb-2" style={{ color: "var(--text-secondary)" }}>
              موضوع پیام:
            </p>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {TOPICS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTopic(t.value)}
                  className="text-xs px-3 py-2 rounded-full text-center"
                  style={{
                    background: topic === t.value ? "rgba(62,232,195,0.15)" : "var(--surface)",
                    color: topic === t.value ? "var(--accent)" : "var(--text-secondary)",
                    border: `1px solid ${topic === t.value ? "var(--accent)" : "var(--surface-border)"}`,
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
              پیام خود را بنویسید، مستقیم برای تیم پشتیبانی ارسال می‌شود.
            </p>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={5}
              placeholder="پیام شما..."
              className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none resize-none"
            />
            <button
              onClick={send}
              disabled={sending || !message.trim()}
              className="mt-3 w-full text-sm px-4 py-2 rounded-full"
              style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
            >
              {sending ? "در حال ارسال..." : "ارسال پیام"}
            </button>
          </>
        )}
      </div>

      <div className="flex flex-col gap-2 items-start">
        <button
          onClick={() => openExternalLink(INSTAGRAM_URL)}
          className="text-xs"
          style={{ color: "var(--accent-violet)" }}
        >
          📸 فالو ما توی اینستاگرام
        </button>
        <button
          onClick={() => navigate("/onboarding")}
          className="text-xs"
          style={{ color: "var(--text-secondary)" }}
        >
          🚀 آموزش تصویری شروع کار
        </button>
        <button
          onClick={() => navigate("/guide")}
          className="text-xs"
          style={{ color: "var(--text-secondary)" }}
        >
          📖 راهنمای کامل NovaTunnel
        </button>
        <button
          onClick={() => navigate("/legal")}
          className="text-xs"
          style={{ color: "var(--text-secondary)" }}
        >
          📄 قوانین استفاده و حریم خصوصی
        </button>
      </div>
    </div>
  );
}
