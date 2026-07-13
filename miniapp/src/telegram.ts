interface TelegramWebApp {
  initData: string;
  platform: string;
  version: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      username?: string;
    };
  };
  ready: () => void;
  expand: () => void;
  openTelegramLink: (url: string) => void;
  openLink: (url: string, options?: { try_instant_view?: boolean }) => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy") => void;
    notificationOccurred: (type: "success" | "error" | "warning") => void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

export function getWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function initTelegram() {
  const app = getWebApp();
  if (!app) return;
  app.ready();
  app.expand();
  try {
    app.setHeaderColor("#050914");
    app.setBackgroundColor("#050914");
  } catch {
    // برخی نسخه‌های قدیمی کلاینت این متد را ندارند
  }
}

export function getInitData(): string {
  return getWebApp()?.initData ?? "";
}

export function haptic(style: "light" | "medium" | "heavy" = "light") {
  getWebApp()?.HapticFeedback?.impactOccurred(style);
}

export function openBotChat(payload?: string) {
  const url = `https://t.me/Milivpnvipbot${payload ? `?start=${payload}` : ""}`;
  const app = getWebApp();
  if (app) app.openTelegramLink(url);
  else window.open(url, "_blank");
}

/** درگاه پرداخت (زرین‌پال) خارج از WebView مینی‌اپ باز می‌شود چون دامنه‌اش با اپ فرق دارد. */
export function openExternalLink(url: string) {
  const app = getWebApp();
  if (app) app.openLink(url);
  else window.open(url, "_blank");
}
