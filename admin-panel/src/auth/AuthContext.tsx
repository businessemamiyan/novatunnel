import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiRequest, clearTokens, getAccessToken, getRefreshToken, storeTokens, ApiError } from "../api";

interface AdminIdentity {
  telegram_id: number;
}

interface TelegramLoginPayload {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

interface AuthContextValue {
  admin: AdminIdentity | null;
  loading: boolean;
  loginWithTelegram: (payload: TelegramLoginPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminIdentity | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      if (!getAccessToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await apiRequest<AdminIdentity>("/api/auth/me");
        setAdmin(me);
      } catch {
        clearTokens();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function loginWithTelegram(payload: TelegramLoginPayload) {
    const tokens = await apiRequest<{ access_token: string; refresh_token: string }>(
      "/api/auth/telegram-login",
      { method: "POST", body: JSON.stringify(payload) },
    );
    storeTokens(tokens.access_token, tokens.refresh_token);
    const me = await apiRequest<AdminIdentity>("/api/auth/me");
    setAdmin(me);
  }

  async function logout() {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) {
        await apiRequest("/api/auth/logout", {
          method: "POST",
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch {
      // حتی اگر ابطال سمت سرور شکست بخورد، سشن محلی باید پاک شود
    } finally {
      clearTokens();
      setAdmin(null);
    }
  }

  return (
    <AuthContext.Provider value={{ admin, loading, loginWithTelegram, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth باید داخل AuthProvider استفاده شود");
  return ctx;
}

export { ApiError };
export type { TelegramLoginPayload };
