import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

import { api } from "../api";

interface Slide {
  emoji: string;
  title: string;
  body: string;
  accent: string;
  bg: string;
}

const SLIDES: Slide[] = [
  {
    emoji: "🚀",
    title: "به NovaTunnel خوش اومدی",
    body: "با ثبت‌نامت، ۱۰,۰۰۰ تومان هدیه خوش‌آمدگویی مستقیم میره تو کیف‌پولت — همین الان قابل استفاده‌ست!",
    accent: "var(--accent)",
    bg: "rgba(62,232,195,0.15)",
  },
  {
    emoji: "🛒",
    title: "اولین سرویستو بخر",
    body: "از «خرید بسته» یکی از بسته‌های حجم رو انتخاب کن، پرداخت کن (یا از هدیه خوش‌آمدگویی استفاده کن) و چند ثانیه بعد سرویست آماده‌ست.",
    accent: "var(--accent-violet)",
    bg: "rgba(155,107,214,0.15)",
  },
  {
    emoji: "🔌",
    title: "وصل شو و لذت ببر",
    body: "کد QR یا لینک اشتراک رو با یکی از اپ‌های پیشنهادی (v2rayNG، Streisand، Hiddify) اسکن کن و در چند ثانیه به اینترنت آزاد وصل شو.",
    accent: "var(--accent)",
    bg: "rgba(62,232,195,0.15)",
  },
  {
    emoji: "🎁",
    title: "دوستاتو دعوت کن، مفت بگیر",
    body: "لینک دعوتتو برای رفقات بفرست — از هر خریدی که اونا (تا ۳ سطح) بزنن، حجم هدیه رایگان می‌گیری. هرچی شبکه‌ت بزرگ‌تر، حجم بیشتر!",
    accent: "var(--accent-violet)",
    bg: "rgba(155,107,214,0.15)",
  },
  {
    emoji: "👑",
    title: "نماینده‌مون شو",
    body: "اگه دوست داری فروش هم بکنی، با فعال‌سازی پنل نمایندگی (۳ رده: نقره‌ای، طلایی، برلیان) می‌تونی حجم بفروشی و سود واقعی به‌دست بیاری.",
    accent: "var(--accent)",
    bg: "rgba(62,232,195,0.15)",
  },
];

export default function Onboarding() {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const navigate = useNavigate();

  const slide = SLIDES[index];
  const isLast = index === SLIDES.length - 1;

  useEffect(() => {
    api.post("/me/onboarding-seen").catch(() => {});
  }, []);

  const go = (dir: number) => {
    const next = index + dir;
    if (next < 0 || next >= SLIDES.length) return;
    setDirection(dir);
    setIndex(next);
  };

  return (
    <div className="p-4 pb-24 flex flex-col" style={{ minHeight: "80vh" }}>
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>

      <div className="flex-1 flex flex-col items-center justify-center">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={index}
            custom={direction}
            initial={{ opacity: 0, x: direction > 0 ? 60 : -60, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: direction > 0 ? -60 : 60, scale: 0.95 }}
            transition={{ duration: 0.35 }}
            className="glass-card p-6 text-center w-full"
            style={{ maxWidth: 380 }}
          >
            <motion.div
              initial={{ scale: 0.5, rotate: -8 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 12 }}
              className="text-6xl mb-4"
            >
              {slide.emoji}
            </motion.div>
            <p className="text-lg font-medium mb-3" style={{ color: slide.accent }}>
              {slide.title}
            </p>
            <p className="text-sm leading-7 m-0" style={{ color: "var(--text-secondary)" }}>
              {slide.body}
            </p>
          </motion.div>
        </AnimatePresence>

        <div className="flex gap-2 mt-6">
          {SLIDES.map((_, i) => (
            <motion.div
              key={i}
              animate={{
                width: i === index ? 24 : 8,
                background: i === index ? slide.accent : "var(--surface-border)",
              }}
              className="h-2 rounded-full"
              transition={{ duration: 0.25 }}
            />
          ))}
        </div>
      </div>

      <div className="flex gap-2 mt-6">
        {index > 0 && (
          <button
            onClick={() => go(-1)}
            className="flex-1 text-sm px-4 py-3 rounded-full"
            style={{ background: "var(--surface)", color: "var(--text-secondary)", border: "1px solid var(--surface-border)" }}
          >
            قبلی
          </button>
        )}
        <button
          onClick={() => (isLast ? navigate("/") : go(1))}
          className="flex-1 text-sm px-4 py-3 rounded-full"
          style={{ background: slide.bg, color: slide.accent }}
        >
          {isLast ? "بزن بریم 🚀" : "بعدی"}
        </button>
      </div>
    </div>
  );
}
