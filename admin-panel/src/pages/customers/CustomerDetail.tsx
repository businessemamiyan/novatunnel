import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { apiRequest, ApiError } from "../../api";
import { usePageMeta } from "../../layout/PageMetaContext";

interface Service {
  id: string;
  label: string;
  is_active: boolean;
  traffic_limit_gb: number;
  traffic_used_gb: number;
  expires_at: string | null;
}

interface CustomerDetailData {
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
  is_agent: boolean;
  agent_tier: string | null;
  direct_referrals_count: number;
  services: Service[];
}

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>();
  usePageMeta("جزئیات مشتری");
  const [data, setData] = useState<CustomerDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [giftAmount, setGiftAmount] = useState("");
  const [giftNote, setGiftNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function load() {
    if (!id) return;
    apiRequest<CustomerDetailData>(`/api/customers/${id}`)
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "خطا در دریافت اطلاعات مشتری"));
  }

  useEffect(load, [id]);

  async function submitGift(e: React.FormEvent) {
    e.preventDefault();
    if (!id) return;
    const amount = Number(giftAmount);
    if (!amount || amount <= 0) {
      setMessage("مقدار حجم را درست وارد کنید");
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      await apiRequest(`/api/customers/${id}/grant-gift`, {
        method: "POST",
        body: JSON.stringify({ amount_gb: amount, note: giftNote || undefined }),
      });
      setGiftAmount("");
      setGiftNote("");
      setMessage("حجم هدیه با موفقیت اعطا شد");
      load();
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "خطا در اعطای حجم هدیه");
    } finally {
      setSubmitting(false);
    }
  }

  if (error) return <p className="badge danger">{error}</p>;
  if (!data) return <p className="text-[var(--text-secondary)]">در حال بارگذاری…</p>;

  return (
    <div className="flex flex-col gap-6">
      <Link to="/customers" className="text-sm text-[var(--accent)]">
        ← بازگشت به لیست مشتریان
      </Link>

      <section className="card grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="stat-label">نام</div>
          <div className="font-semibold">{data.full_name || "—"}</div>
        </div>
        <div>
          <div className="stat-label">آیدی تلگرام</div>
          <div className="font-semibold">
            {data.telegram_username ? `@${data.telegram_username}` : `#${data.telegram_id}`}
          </div>
        </div>
        <div>
          <div className="stat-label">موبایل</div>
          <div className="font-semibold">
            {data.phone_number || "—"}{" "}
            {data.phone_verified ? (
              <span className="badge success">تایید</span>
            ) : (
              <span className="badge warning">تاییدنشده</span>
            )}
          </div>
        </div>
        <div>
          <div className="stat-label">نوع حساب</div>
          <div className="font-semibold">
            {data.is_agent ? <span className="badge info">نماینده · {data.agent_tier}</span> : "مشتری عادی"}
          </div>
        </div>
        <div>
          <div className="stat-label">موجودی کیف‌پول</div>
          <div className="font-semibold">{data.wallet_balance_toman.toLocaleString("fa-IR")} تومان</div>
        </div>
        <div>
          <div className="stat-label">حجم هدیه فعلی</div>
          <div className="font-semibold">{data.gift_balance_gb.toFixed(2)} گیگ</div>
        </div>
        <div>
          <div className="stat-label">زیرمجموعه مستقیم</div>
          <div className="font-semibold">{data.direct_referrals_count.toLocaleString("fa-IR")} نفر</div>
        </div>
        <div>
          <div className="stat-label">عضویت</div>
          <div className="font-semibold">{new Date(data.created_at).toLocaleDateString("fa-IR")}</div>
        </div>
      </section>

      <section className="card">
        <h2 className="font-bold mb-4">سرویس‌ها</h2>
        {data.services.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">هیچ سرویسی ثبت نشده است.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>عنوان</th>
                  <th>وضعیت</th>
                  <th>مصرف</th>
                  <th>انقضا</th>
                </tr>
              </thead>
              <tbody>
                {data.services.map((s) => (
                  <tr key={s.id}>
                    <td>{s.label}</td>
                    <td>
                      {s.is_active ? (
                        <span className="badge success">فعال</span>
                      ) : (
                        <span className="badge danger">غیرفعال</span>
                      )}
                    </td>
                    <td>
                      {s.traffic_used_gb.toFixed(1)} از {s.traffic_limit_gb.toFixed(1)} گیگ
                    </td>
                    <td>{s.expires_at ? new Date(s.expires_at).toLocaleDateString("fa-IR") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card max-w-md">
        <h2 className="font-bold mb-4">اعطای دستی حجم هدیه</h2>
        <form className="flex flex-col gap-3" onSubmit={submitGift}>
          <input
            className="input"
            type="number"
            step="0.1"
            min="0"
            placeholder="مقدار (گیگابایت)"
            value={giftAmount}
            onChange={(e) => setGiftAmount(e.target.value)}
          />
          <input
            className="input"
            placeholder="یادداشت (اختیاری)"
            value={giftNote}
            onChange={(e) => setGiftNote(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "در حال ثبت…" : "اعطا کن"}
          </button>
          {message && <p className="text-sm text-[var(--text-secondary)]">{message}</p>}
        </form>
      </section>
    </div>
  );
}
