import { getInitData } from "./telegram";

const BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": getInitData(),
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

/** آپلود عکس (رسید پرداخت) — نباید Content-Type دستی ست بشه تا مرورگر خودش boundary مولتی‌پارت رو بسازه. */
export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "X-Telegram-Init-Data": getInitData() },
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

/** تصاویر (QR، عکس رسید) نیاز به هدر initData دارند که <img src> نمی‌تواند بفرستد؛
 * پس به‌صورت blob گرفته و object URL موقت ساخته می‌شود. */
async function fetchImageObjectUrl(path: string): Promise<string> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "X-Telegram-Init-Data": getInitData() },
  });
  if (!res.ok) throw new Error(`${res.status}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export function fetchQrImage(panelId: string): Promise<string> {
  return fetchImageObjectUrl(`/my/services/${panelId}/qr`);
}

export function fetchReceiptPhoto(purchaseId: string): Promise<string> {
  return fetchImageObjectUrl(`/receipts/${purchaseId}/photo`);
}

/** دانلود فایل (اکسل و مشابه) — نیاز به هدر initData دارد که لینک <a href> مستقیم نمی‌تواند بفرستد. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "X-Telegram-Init-Data": getInitData() },
  });
  if (!res.ok) throw new Error(`${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
