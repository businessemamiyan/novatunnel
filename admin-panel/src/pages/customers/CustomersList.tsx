import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest, ApiError, API_BASE, getAccessToken } from "../../api";
import { usePageMeta } from "../../layout/PageMetaContext";

interface Customer {
  id: string;
  telegram_id: number;
  telegram_username: string | null;
  full_name: string | null;
  phone_number: string | null;
  phone_verified: boolean;
  wallet_balance_toman: number;
  gift_balance_gb: number;
  last_purchase_at: string | null;
  created_at: string;
}

const PAGE_SIZE = 20;

export default function CustomersList() {
  usePageMeta("مشتریان", "جست‌وجو، مشاهده و مدیریت مشتریان NovaTunnel");
  const [items, setItems] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true);
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(page * PAGE_SIZE),
      });
      if (search.trim()) params.set("search", search.trim());

      apiRequest<{ total: number; items: Customer[] }>(`/api/customers?${params}`)
        .then((res) => {
          setItems(res.items);
          setTotal(res.total);
          setError(null);
        })
        .catch((e) => setError(e instanceof ApiError ? e.message : "خطا در دریافت مشتریان"))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(handle);
  }, [search, page]);

  async function handleExport() {
    const token = getAccessToken();
    const res = await fetch(`${API_BASE}/api/customers/export`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "novatunnel_customers.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  }

  const totalPages = Math.max(Math.ceil(total / PAGE_SIZE), 1);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <input
          className="input w-full max-w-xs"
          placeholder="جست‌وجو با نام، یوزرنیم، شماره یا آیدی عددی…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
        />
        <button className="btn btn-secondary" onClick={handleExport}>
          خروجی اکسل
        </button>
      </div>

      {error && <p className="badge danger">{error}</p>}

      <div className="card !p-0 overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>مشتری</th>
              <th>موبایل</th>
              <th>کیف‌پول</th>
              <th>حجم هدیه</th>
              <th>آخرین خرید</th>
              <th>عضویت</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>
                  <Link to={`/customers/${c.id}`} className="text-[var(--accent)] font-medium">
                    {c.full_name || c.telegram_username || `#${c.telegram_id}`}
                  </Link>
                  {c.telegram_username && (
                    <div className="text-xs text-[var(--text-secondary)]">@{c.telegram_username}</div>
                  )}
                </td>
                <td>
                  {c.phone_number || "—"}{" "}
                  {c.phone_verified ? (
                    <span className="badge success">تایید</span>
                  ) : (
                    <span className="badge warning">تاییدنشده</span>
                  )}
                </td>
                <td>{c.wallet_balance_toman.toLocaleString("fa-IR")} ت</td>
                <td>{c.gift_balance_gb.toFixed(2)} گیگ</td>
                <td>{c.last_purchase_at ? new Date(c.last_purchase_at).toLocaleDateString("fa-IR") : "—"}</td>
                <td>{new Date(c.created_at).toLocaleDateString("fa-IR")}</td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-[var(--text-secondary)] py-8">
                  مشتری‌ای پیدا نشد.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-[var(--text-secondary)]">
        <span>
          {total.toLocaleString("fa-IR")} مشتری · صفحه {(page + 1).toLocaleString("fa-IR")} از{" "}
          {totalPages.toLocaleString("fa-IR")}
        </span>
        <div className="flex gap-2">
          <button
            className="btn btn-secondary"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(p - 1, 0))}
          >
            قبلی
          </button>
          <button
            className="btn btn-secondary"
            disabled={page + 1 >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            بعدی
          </button>
        </div>
      </div>
    </div>
  );
}
