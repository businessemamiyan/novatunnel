import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, uploadFile } from "../api";
import { Me, WalletTopup } from "../types";
import { openExternalLink } from "../telegram";
import CopyButton from "../components/CopyButton";

const PRESET_AMOUNTS = [100000, 250000, 500000, 1000000];

const STATUS_LABELS: Record<string, string> = {
  pending: "⏳ در انتظار تایید",
  confirmed: "✅ تایید شد",
  rejected: "❌ رد شد",
};

export default function WalletPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [history, setHistory] = useState<WalletTopup[]>([]);
  const [amount, setAmount] = useState<number>(PRESET_AMOUNTS[0]);
  const [customAmount, setCustomAmount] = useState("");
  const [invoice, setInvoice] = useState<{ id: string; amount_toman: number; card_number: string; card_holder: string; payment_notice?: string } | null>(null);
  const [uploaded, setUploaded] = useState(false);
  const [onlinePayError, setOnlinePayError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const load = () => {
    api.get<Me>("/me").then(setMe);
    api.get<WalletTopup[]>("/wallet-topup/mine").then(setHistory);
  };
  useEffect(load, []);

  const finalAmount = customAmount ? Number(customAmount) : amount;

  const createInvoice = async () => {
    if (!finalAmount || finalAmount <= 0) return;
    const res = await api.post<{ id: string; amount_toman: number; card_number: string; card_holder: string; payment_notice?: string }>(
      "/wallet-topup",
      { amount_toman: finalAmount },
    );
    setInvoice(res);
    setUploaded(false);
    setOnlinePayError("");
  };

  const payOnline = async () => {
    if (!invoice) return;
    setOnlinePayError("");
    try {
      const res = await api.post<{ payment_url: string }>(`/wallet-topup/${invoice.id}/pay-online`);
      openExternalLink(res.payment_url);
    } catch (e) {
      setOnlinePayError(e instanceof Error ? e.message : "پرداخت آنلاین در دسترس نیست");
    }
  };

  const onFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !invoice) return;
    await uploadFile(`/wallet-topup/${invoice.id}/receipt`, file);
    setUploaded(true);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>

      <div className="glass-card p-4 mb-4">
        <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
          موجودی کیف‌پول شما
        </p>
        <p className="text-2xl font-medium m-0" style={{ color: "var(--accent-violet)" }}>
          {(me?.wallet_balance_toman ?? 0).toLocaleString("fa-IR")} تومان
        </p>
      </div>

      <button
        onClick={() => navigate("/agency")}
        className="glass-card p-4 mb-4 w-full text-right"
        style={{ color: "var(--accent-violet)" }}
      >
        🏷 پنل نمایندگی
      </button>

      {!!me?.reward_credit_toman && (
        <div className="glass-card p-4 mb-4">
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            🎁 اعتبار پاداش (فقط برای خرید بسته حجم)
          </p>
          <p className="text-2xl font-medium m-0" style={{ color: "var(--accent)" }}>
            {me.reward_credit_toman.toLocaleString("fa-IR")} تومان
          </p>
        </div>
      )}

      {!invoice ? (
        <div className="glass-card p-4 mb-4">
          <p className="text-sm font-medium mb-3">افزایش موجودی</p>
          <div className="grid grid-cols-2 gap-2 mb-3">
            {PRESET_AMOUNTS.map((a) => (
              <button
                key={a}
                onClick={() => {
                  setAmount(a);
                  setCustomAmount("");
                }}
                className="text-sm px-3 py-2 rounded-full"
                style={{
                  background: !customAmount && amount === a ? "rgba(62,232,195,0.15)" : "var(--surface)",
                  color: !customAmount && amount === a ? "var(--accent)" : "var(--text-secondary)",
                  border: `1px solid ${!customAmount && amount === a ? "var(--accent)" : "var(--surface-border)"}`,
                }}
              >
                {a.toLocaleString("fa-IR")} تومان
              </button>
            ))}
          </div>
          <input
            type="number"
            placeholder="مبلغ دلخواه (تومان)"
            value={customAmount}
            onChange={(e) => setCustomAmount(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3"
          />
          <button
            onClick={createInvoice}
            className="w-full text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
          >
            ساخت فاکتور شارژ
          </button>
        </div>
      ) : (
        <div className="glass-card p-4 mb-4">
          <p className="text-sm font-medium mb-2">💳 پرداخت کارت‌به‌کارت</p>
          <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            مبلغ {invoice.amount_toman.toLocaleString("fa-IR")} تومان را به شماره کارت زیر واریز کنید و رسید را
            آپلود کنید:
          </p>
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm m-0" dir="ltr">💳 {invoice.card_number}</p>
            <CopyButton text={invoice.card_number} />
          </div>
          <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            به نام: {invoice.card_holder}
          </p>
          {invoice.payment_notice && (
            <p className="text-[11px] mb-3" style={{ color: "var(--danger)" }}>
              {invoice.payment_notice}
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
          <p className="text-[11px] mb-3 text-center" style={{ color: "var(--text-secondary)" }}>
            یا کارت‌به‌کارت:
          </p>

          {uploaded ? (
            <p className="text-sm text-center py-2" style={{ color: "var(--accent)" }}>
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
          <button
            onClick={() => setInvoice(null)}
            className="w-full text-xs mt-2"
            style={{ color: "var(--text-secondary)" }}
          >
            انصراف / ساخت فاکتور جدید
          </button>
        </div>
      )}

      <p className="font-medium mb-2">گردش کیف‌پول</p>
      {history.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          هنوز درخواستی ثبت نشده.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {history.map((h) => (
            <div key={h.id} className="glass-card p-3 flex items-center justify-between">
              <span className="text-sm">{h.amount_toman.toLocaleString("fa-IR")} تومان</span>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                {STATUS_LABELS[h.status] || h.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
