import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import { api } from "../api";
import { Me, NetworkData } from "../types";
import NetworkTree from "../components/NetworkTree";
import { haptic } from "../telegram";

const LEVEL_COLORS: Record<string, string> = {
  "1": "#3ee8c3",
  "2": "#7fd8c9",
  "3": "#9b6bd6",
};

const LEVEL_MAX: Record<string, number> = { "1": 4, "2": 16, "3": 64 };

export default function Network() {
  const [me, setMe] = useState<Me | null>(null);
  const [data, setData] = useState<NetworkData | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.get<Me>("/me").then(setMe);
    api.get<NetworkData>("/my/network").then(setData);
  }, []);

  const total = data ? data.level1.length + data.level2.length + data.level3.length : 0;
  const link = me ? `https://t.me/Milivpnvipbot?start=ref_${me.telegram_id}` : "";

  const copyLink = async () => {
    if (!link) return;
    await navigator.clipboard.writeText(link);
    haptic("light");
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const shareLink = () => {
    if (!link) return;
    const text = encodeURIComponent("با این لینک بیا NovaTunnel و حجم رایگان بگیر 🎁");
    window.open(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${text}`, "_blank");
  };

  return (
    <div className="p-4 pb-24">
      <p className="text-lg font-medium mb-4">🌐 شبکه زیرمجموعه من</p>

      {/* هدر گرافیکی: مجموع شبکه */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card py-8 mb-4 flex flex-col items-center relative overflow-hidden"
      >
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(circle at 50% 30%, rgba(62,232,195,0.18), transparent 60%), radial-gradient(circle at 70% 80%, rgba(155,107,214,0.15), transparent 55%)",
          }}
        />
        <div className="relative z-10 flex flex-col items-center">
          <div
            className="w-24 h-24 rounded-full flex items-center justify-center mb-3"
            style={{
              background: "conic-gradient(from 0deg, #3ee8c3, #9b6bd6, #3ee8c3)",
              boxShadow: "0 0 30px rgba(62,232,195,0.35)",
            }}
          >
            <div
              className="w-[84px] h-[84px] rounded-full flex items-center justify-center"
              style={{ background: "var(--bg-deep)" }}
            >
              <span className="text-2xl font-bold">{total}</span>
            </div>
          </div>
          <p className="text-sm m-0" style={{ color: "var(--text-secondary)" }}>
            نفر در کل شبکه شما
          </p>
        </div>
      </motion.div>

      {/* لینک دعوت */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass-card p-4 mb-4"
      >
        <p className="text-xs mb-2" style={{ color: "var(--text-secondary)" }}>
          🎁 لینک اختصاصی دعوت — با هر خرید زیرمجموعه‌تان، حجم هدیه رایگان می‌گیرید
        </p>
        <p
          className="text-xs p-2 rounded-lg mb-3 truncate"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--surface-border)" }}
          dir="ltr"
        >
          {link || "..."}
        </p>
        <div className="flex gap-2">
          <button
            onClick={copyLink}
            className="flex-1 text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
          >
            {copied ? "کپی شد ✅" : "📋 کپی لینک"}
          </button>
          <button
            onClick={shareLink}
            className="flex-1 text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
          >
            📤 اشتراک‌گذاری
          </button>
        </div>
      </motion.div>

      {!data ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          در حال بارگذاری...
        </p>
      ) : (
        <>
          {/* کارت‌های خلاصه هر سطح */}
          <div className="flex flex-col gap-3 mb-5">
            {(["1", "2", "3"] as const).map((level, i) => {
              const people = level === "1" ? data.level1 : level === "2" ? data.level2 : data.level3;
              const meta = data.levels_meta[level];
              const color = LEVEL_COLORS[level];
              const max = LEVEL_MAX[level];
              const capPercent = meta && meta.monthly_cap_gb > 0
                ? Math.min((meta.earned_this_month_gb / meta.monthly_cap_gb) * 100, 100)
                : 0;

              return (
                <motion.div
                  key={level}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.05 }}
                  className="glass-card p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ background: color, boxShadow: `0 0 8px ${color}` }}
                      />
                      <p className="text-sm font-medium m-0" style={{ color }}>
                        سطح {level}
                      </p>
                      {meta && (
                        <span className="text-[10px]" style={{ color: "var(--text-secondary)" }}>
                          ({meta.reward_percent}٪ پاداش)
                        </span>
                      )}
                    </div>
                    <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      {people.length} از {max} نفر
                    </span>
                  </div>

                  {meta && (
                    <>
                      <div
                        className="w-full h-1.5 rounded-full mb-1 overflow-hidden"
                        style={{ background: "rgba(255,255,255,0.06)" }}
                      >
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${capPercent}%` }}
                          transition={{ duration: 0.6 }}
                          className="h-full rounded-full"
                          style={{ background: color }}
                        />
                      </div>
                      <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>
                        {meta.earned_this_month_gb.toFixed(1)} از {meta.monthly_cap_gb} گیگ سقف این ماه
                      </p>
                    </>
                  )}
                </motion.div>
              );
            })}
          </div>

          <NetworkTree level={1} people={data.level1} />
          <NetworkTree level={2} people={data.level2} />
          <NetworkTree level={3} people={data.level3} />
        </>
      )}
    </div>
  );
}
