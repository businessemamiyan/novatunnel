import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, type TelegramLoginPayload } from "./AuthContext";

declare global {
  interface Window {
    onNovaTunnelTelegramAuth?: (user: TelegramLoginPayload) => void;
  }
}

const BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || "";

export default function LoginPage() {
  const { loginWithTelegram } = useAuth();
  const navigate = useNavigate();
  const widgetContainer = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    window.onNovaTunnelTelegramAuth = async (user) => {
      setError(null);
      setVerifying(true);
      try {
        await loginWithTelegram(user);
        navigate("/", { replace: true });
      } catch (e) {
        setError(e instanceof Error ? e.message : "ورود ناموفق بود");
      } finally {
        setVerifying(false);
      }
    };

    if (widgetContainer.current) {
      widgetContainer.current.innerHTML = "";
      const script = document.createElement("script");
      script.src = "https://telegram.org/js/telegram-widget.js?22";
      script.async = true;
      script.setAttribute("data-telegram-login", BOT_USERNAME);
      script.setAttribute("data-size", "large");
      script.setAttribute("data-radius", "10");
      script.setAttribute("data-onauth", "onNovaTunnelTelegramAuth(user)");
      script.setAttribute("data-request-access", "write");
      widgetContainer.current.appendChild(script);
    }

    return () => {
      delete window.onNovaTunnelTelegramAuth;
    };
  }, [loginWithTelegram, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="card w-full max-w-sm text-center">
        <h1 className="text-xl font-bold mb-1">ورود به پنل مدیریت</h1>
        <p className="text-[var(--text-secondary)] text-sm mb-6">
          فقط ادمین‌های ثبت‌شدهٔ NovaTunnel با حساب تلگرام خودشان می‌توانند وارد شوند.
        </p>

        {!BOT_USERNAME && (
          <p className="badge danger mb-4">VITE_TELEGRAM_BOT_USERNAME تنظیم نشده است</p>
        )}

        <div className="flex justify-center min-h-[46px] items-center" ref={widgetContainer} />

        {verifying && <p className="text-sm text-[var(--text-secondary)] mt-4">در حال تایید…</p>}
        {error && <p className="badge danger mt-4 inline-block">{error}</p>}
      </div>
    </div>
  );
}
