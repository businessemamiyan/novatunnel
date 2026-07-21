const API_BASE = import.meta.env.VITE_PANEL_API_BASE_URL || "http://localhost:8001";

const ACCESS_KEY = "novatunnel_panel_access_token";
const REFRESH_KEY = "novatunnel_panel_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function storeTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const res = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) {
    clearTokens();
    return false;
  }
  const data = await res.json();
  storeTokens(data.access_token, data.refresh_token);
  return true;
}

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestInit = {},
  { retry = true }: { retry?: boolean } = {},
): Promise<T> {
  const accessToken = getAccessToken();
  const headers = new Headers(options.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && retry) {
    refreshPromise = refreshPromise || refreshTokens();
    const refreshed = await refreshPromise;
    refreshPromise = null;
    if (refreshed) {
      return apiRequest<T>(path, options, { retry: false });
    }
    clearTokens();
    window.location.assign("/login");
    throw new ApiError(401, "احراز هویت منقضی شده است");
  }

  if (!res.ok) {
    let message = `خطای سرور (${res.status})`;
    try {
      const body = await res.json();
      message = body.detail || message;
    } catch {
      // پاسخ JSON نبود، از پیام پیش‌فرض استفاده می‌شود
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.blob()) as T;
}

export { ApiError, API_BASE };
