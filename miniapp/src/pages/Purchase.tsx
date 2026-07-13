import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { api, uploadFile } from "../api";
import { Package, PurchaseCreateResponse } from "../types";
import { openExternalLink } from "../telegram";
import CopyButton from "../components/CopyButton";

type Step = "plan" | "payment" | "connect";

const STEPS: { key: Step; label: string }[] = [
  { key: "plan", label: "۱. انتخاب پلن" },
  { key: "payment", label: "۲. پرداخت" },
  { key: "connect", label: "۳. اتصال" },
];

export default function Purchase() {
  const [params] = useSearchParams();
  const renewedPanelId = params.get("renew");
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>("plan");
  const [packages, setPackages] = useState<Package[]>([]);
  const [selected, setSelected] = useState<Package | null>(null);
  const [serviceLabel, setServiceLabel] = useState("");
  const [discountCode, setDiscountCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<PurchaseCreateResponse | null>(null);
  const [uploaded, setUploaded] = useState(false);
  const [onlinePayError, setOnlinePayError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get<Package[]>("/my/packages").then(setPackages);
  }, []);

  const choosePackage = (p: Package) => {
    setSelected(p);
    setStep("payment");
  };

  const submitPurchase = async () => {
    if (!selected) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await api.post<PurchaseCreateResponse>("/purchases", {
        package_id: selected.id,
        service_label: renewedPanelId ? undefined : serviceLabel.trim() || undefined,
        discount_code: discountCode.trim() || undefined,
        renewed_panel_id: renewedPanelId || undefined,
      });
      setResult(res);
      setStep("connect");
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطایی رخ داد");
    } finally {
      setSubmitting(false);
    }
  };

  const onFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !result) return;
    await uploadFile(`/purchases/${result.id}/receipt`, file);
    setUploaded(true);
  };

  const payOnline = async () => {
    if (!result) return;
    setOnlinePayError("");
    try {
      const res = await api.post<{ payment_url: string }>(`/purchases/${result.id}/pay-online`);
      openExternalLink(res.payment_url);
    } catch (e) {
      setOnlinePayError(e instanceof Error ? e.message : "پرداخت آنلاین در دسترس نیست");
    }
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>

      <div className="flex gap-2 mb-5">
        {STEPS.map((s) => (
          <div
            key={s.key}
            className="flex-1 text-center text-xs py-2 rounded-full"
            style={{
              background: step === s.key ? "rgba(62,232,195,0.15)" : "var(--surface)",
              color: step === s.key ? "var(--accent)" : "var(--text-secondary)",
              border: `1px solid ${step === s.key ? "var(--accent)" : "var(--surface-border)"}`,
            }}
          >
            {s.label}
          </div>
        ))}
      </div>

      {step === "plan" && (
        <div className="flex flex-col gap-3">
          {packages.map((p) => (
            <button
              key={p.id}
              onClick={() => choosePackage(p)}
              className="glass-card p-4 text-right"
            >
              <div className="flex items-center justify-between mb-1">
                <p className="font-medium m-0">{p.name}</p>
                {p.badge && (
                  <span
                    className="text-[11px] px-2 py-1 rounded-full"
                    style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
                  >
                    {p.badge}
                  </span>
                )}
              </div>
              <p className="text-sm m-0" style={{ color: "var(--accent)" }}>
                {p.retail_price_toman.toLocaleString("fa-IR")} تومان
              </p>
            </button>
          ))}
        </div>
      )}

      {step === "payment" && selected && (
        <div className="glass-card p-4">
          <p className="font-medium mb-1">{selected.name}</p>
          <p className="text-sm mb-4" style={{ color: "var(--accent)" }}>
            {selected.retail_price_toman.toLocaleString("fa-IR")} تومان
          </p>

          {!renewedPanelId && (
            <>
              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                اسم دلخواه برای این سرویس
              </label>
              <input
                type="text"
                value={serviceLabel}
                onChange={(e) => setServiceLabel(e.target.value)}
                placeholder="مثلاً «گوشی من»"
                className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
              />
            </>
          )}

          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
            کد تخفیف (اختیاری)
          </label>
          <input
            type="text"
            value={discountCode}
            onChange={(e) => setDiscountCode(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          />

          <p className="text-[11px] mb-3" style={{ color: "var(--text-secondary)" }}>
            💡 موجودی کیف‌پول شما به‌صورت خودکار به‌عنوان تخفیف از مبلغ کسر می‌شود.
          </p>

          {error && (
            <p className="text-xs mb-3" style={{ color: "var(--danger)" }}>
              {error}
            </p>
          )}

          <button
            onClick={submitPurchase}
            disabled={submitting}
            className="w-full text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
          >
            {submitting ? "در حال ثبت..." : "ادامه و پرداخت"}
          </button>
        </div>
      )}

      {step === "connect" && result && (
        <div className="glass-card p-4 text-center">
          {result.status === "auto_approved" ? (
            <>
              <p className="text-2xl mb-2">🎉</p>
              <p className="text-sm mb-4" style={{ color: "var(--accent)" }}>
                کل مبلغ از کیف‌پول شما پرداخت شد! سرویس شما در حال آماده‌سازی است و به‌زودی در تلگرام برایتان
                ارسال می‌شود.
              </p>
              <button
                onClick={() => navigate("/services")}
                className="w-full text-sm px-4 py-2 rounded-full"
                style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
              >
                مشاهده سرویس‌های من
              </button>
            </>
          ) : (
            <>
              {!!result.reward_credit_used && (
                <p className="text-xs mb-1" style={{ color: "var(--accent)" }}>
                  🎁 {result.reward_credit_used.toLocaleString("fa-IR")} تومان از اعتبار پاداش شما کسر شد
                </p>
              )}
              <p className="text-sm mb-2">لطفاً مبلغ زیر را به شماره کارت واریز کنید:</p>
              <p className="text-lg font-medium mb-2">
                {result.final_price.toLocaleString("fa-IR")} تومان
              </p>
              <div className="flex items-center justify-center gap-2 mb-1">
                <p className="text-sm m-0" dir="ltr">💳 {result.card_number}</p>
                {result.card_number && <CopyButton text={result.card_number} />}
              </div>
              <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
                به نام: {result.card_holder}
              </p>
              {result.payment_notice && (
                <p className="text-[11px] mb-3" style={{ color: "var(--danger)" }}>
                  {result.payment_notice}
                </p>
              )}

              <button
                onClick={payOnline}
                className="w-full text-sm px-4 py-2 rounded-full mb-2"
                style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
              >
                ⚡ پرداخت آنلاین (زرین‌پال)
              </button>
              {onlinePayError && (
                <p className="text-[11px] mb-2" style={{ color: "var(--danger)" }}>
                  {onlinePayError}
                </p>
              )}
              <p className="text-[11px] mb-4 text-center" style={{ color: "var(--text-secondary)" }}>
                یا کارت‌به‌کارت:
              </p>

              {uploaded ? (
                <p className="text-sm" style={{ color: "var(--accent)" }}>
                  ✅ رسید ارسال شد، در حال بررسی توسط ادمین است.
                </p>
              ) : (
                <>
                  <input ref={fileRef} type="file" accept="image/*" onChange={onFileChange} className="hidden" />
                  <button
                    onClick={() => fileRef.current?.click()}
                    className="w-full text-sm px-4 py-2 rounded-full"
                    style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
                  >
                    📷 آپلود عکس رسید
                  </button>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
