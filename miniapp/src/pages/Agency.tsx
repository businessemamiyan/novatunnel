import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, uploadFile } from "../api";
import { openExternalLink } from "../telegram";
import {
  AgencyActivationResponse, AgencyCustomer, AgencyStatus, AgencyTierConfig, AgentAccounting, AgentPlanPrice,
  Expense, PaymentCard,
} from "../types";
import CopyButton from "../components/CopyButton";

const TIER_LABELS: Record<string, string> = {
  silver: "🥈 نقره‌ای",
  gold: "🥇 طلایی",
  diamond: "💎 برلیان",
  vip: "🛡 ویژه",
};

const TIER_ORDER: Record<string, number> = { silver: 1, gold: 2, diamond: 3, vip: 4 };

type Tab = "dashboard" | "sell" | "customers" | "downline" | "link" | "pricing" | "cards" | "accounting";

const TABS: { key: Tab; label: string }[] = [
  { key: "dashboard", label: "داشبورد" },
  { key: "sell", label: "فروش جدید" },
  { key: "customers", label: "مشتریان من" },
  { key: "downline", label: "زیرمجموعه" },
  { key: "link", label: "لینک من" },
  { key: "pricing", label: "قیمت‌گذاری" },
  { key: "cards", label: "💳 کارت‌های من" },
  { key: "accounting", label: "💼 حسابداری" },
];

const EXPENSE_CATEGORIES = ["تبلیغات", "برداشت شخصی", "سایر"];

export default function Agency() {
  const [status, setStatus] = useState<AgencyStatus | null>(null);
  const [tiers, setTiers] = useState<AgencyTierConfig[]>([]);
  const [activation, setActivation] = useState<AgencyActivationResponse | null>(null);
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("dashboard");
  const [customers, setCustomers] = useState<AgencyCustomer[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // فرم فروش به مشتری
  const [customerId, setCustomerId] = useState("");
  const [volumeGb, setVolumeGb] = useState("");
  const [priceToman, setPriceToman] = useState("");
  const [isGiftResale, setIsGiftResale] = useState(false);
  const [isVipService, setIsVipService] = useState(false);
  const [serviceLabel, setServiceLabel] = useState("");
  const [resaleResult, setResaleResult] = useState("");
  const [resaleError, setResaleError] = useState("");

  // لینک اختصاصی
  const [slugInput, setSlugInput] = useState("");
  const [slugError, setSlugError] = useState("");
  const [slugCopied, setSlugCopied] = useState(false);

  // قیمت‌گذاری
  const [pricing, setPricing] = useState<AgentPlanPrice[]>([]);
  const [priceEdits, setPriceEdits] = useState<Record<number, string>>({});
  const [priceSaved, setPriceSaved] = useState<Record<number, string>>({});

  // حسابداری
  const [accounting, setAccounting] = useState<AgentAccounting | null>(null);
  const [expenseAmount, setExpenseAmount] = useState("");
  const [expenseDesc, setExpenseDesc] = useState("");
  const [expenseCategory, setExpenseCategory] = useState(EXPENSE_CATEGORIES[0]);
  const [expenseError, setExpenseError] = useState("");

  // کارت‌های پرداخت من
  const [cards, setCards] = useState<PaymentCard[]>([]);
  const [newCardNumber, setNewCardNumber] = useState("");
  const [newCardHolder, setNewCardHolder] = useState("");
  const [cardError, setCardError] = useState("");

  const load = () => {
    api.get<AgencyStatus>("/agency/me").then(setStatus);
    api.get<AgencyTierConfig[]>("/agency/tiers").then(setTiers);
  };
  useEffect(load, []);

  const loadAccounting = () => api.get<AgentAccounting>("/agency/accounting").then(setAccounting);
  const loadCards = () => api.get<PaymentCard[]>("/agency/payment-cards").then(setCards);

  useEffect(() => {
    if (tab === "customers" && status?.is_agent) {
      api.get<AgencyCustomer[]>("/agency/customers").then(setCustomers);
    }
    if (tab === "pricing" && status?.is_agent) {
      api.get<AgentPlanPrice[]>("/agency/pricing").then(setPricing);
    }
    if (tab === "accounting" && status?.is_agent) {
      loadAccounting();
    }
    if (tab === "cards" && status?.is_agent) {
      loadCards();
    }
  }, [tab, status?.is_agent]);

  const addCard = async () => {
    setCardError("");
    if (!newCardNumber.trim() || !newCardHolder.trim()) {
      setCardError("لطفاً هم شماره کارت و هم نام صاحب کارت را وارد کنید.");
      return;
    }
    try {
      await api.post("/agency/payment-cards", { card_number: newCardNumber.trim(), card_holder: newCardHolder.trim() });
      setNewCardNumber("");
      setNewCardHolder("");
      loadCards();
    } catch (e) {
      setCardError(e instanceof Error ? e.message : "خطا در افزودن کارت");
    }
  };

  const toggleCardActive = async (c: PaymentCard) => {
    await api.patch(`/agency/payment-cards/${c.id}`, {
      card_number: c.card_number, card_holder: c.card_holder, is_active: !c.is_active,
    });
    loadCards();
  };

  const removeCard = async (id: number) => {
    await api.delete(`/agency/payment-cards/${id}`);
    loadCards();
  };

  const addExpense = async () => {
    setExpenseError("");
    const amount = Number(expenseAmount);
    if (!amount || amount <= 0 || !expenseDesc.trim()) {
      setExpenseError("مبلغ و توضیح را وارد کنید.");
      return;
    }
    try {
      await api.post<Expense>("/agency/accounting/expenses", {
        amount_toman: amount,
        description: expenseDesc.trim(),
        category: expenseCategory,
      });
      setExpenseAmount("");
      setExpenseDesc("");
      loadAccounting();
    } catch (e) {
      setExpenseError(e instanceof Error ? e.message : "خطا در ثبت هزینه");
    }
  };

  const removeExpense = async (id: string) => {
    await api.delete(`/agency/accounting/expenses/${id}`);
    loadAccounting();
  };

  const agentLink = status?.agent_slug
    ? `https://t.me/Milivpnvipbot?start=agent_${status.agent_slug}`
    : "";

  const saveSlug = async () => {
    setSlugError("");
    try {
      await api.post("/agency/slug", { slug: slugInput.trim() });
      load();
    } catch (e) {
      setSlugError(e instanceof Error ? e.message : "خطا در ثبت شناسه");
    }
  };

  const copyLink = async () => {
    if (!agentLink) return;
    await navigator.clipboard.writeText(agentLink);
    setSlugCopied(true);
    setTimeout(() => setSlugCopied(false), 1500);
  };

  const shareLink = () => {
    if (!agentLink) return;
    const text = "اینترنت پرسرعت و پایدار با قیمت ویژه من 🎁";
    openExternalLink(`https://t.me/share/url?url=${encodeURIComponent(agentLink)}&text=${encodeURIComponent(text)}`);
  };

  const savePrice = async (packageId: number) => {
    const raw = priceEdits[packageId];
    if (!raw) return;
    try {
      await api.post("/agency/pricing", { package_id: packageId, price_toman: Number(raw) });
      setPriceSaved((prev) => ({ ...prev, [packageId]: "✅ ذخیره شد" }));
      api.get<AgentPlanPrice[]>("/agency/pricing").then(setPricing);
    } catch (e) {
      setPriceSaved((prev) => ({ ...prev, [packageId]: e instanceof Error ? e.message : "خطا" }));
    }
  };

  const requestActivation = async (tier: string) => {
    setError("");
    try {
      const res = await api.post<AgencyActivationResponse>("/agency/activate", { tier });
      setActivation(res);
      setUploaded(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطا در ثبت درخواست");
    }
  };

  const onFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activation) return;
    await uploadFile(`/agency/activate/${activation.id}/receipt`, file);
    setUploaded(true);
  };

  const submitResale = async () => {
    setResaleError("");
    setResaleResult("");
    const vol = Number(volumeGb);
    const price = Number(priceToman);
    if (!customerId || !vol || !price) {
      setResaleError("همه فیلدها را پر کنید.");
      return;
    }
    try {
      const res = await api.post<{ id: string; panel_status: string }>("/agency/resell", {
        customer_telegram_id: Number(customerId),
        volume_gb: vol,
        price_toman: price,
        is_gift_resale: isGiftResale,
        service_label: serviceLabel || undefined,
        is_vip_service: isVipService,
      });
      setResaleResult(res.panel_status);
      setCustomerId("");
      setVolumeGb("");
      setPriceToman("");
      setServiceLabel("");
      setIsVipService(false);
      load();
    } catch (e) {
      setResaleError(e instanceof Error ? e.message : "خطا در ثبت فروش");
    }
  };

  if (!status) {
    return (
      <div className="p-4 pb-24">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>در حال بارگذاری...</p>
      </div>
    );
  }

  // هنوز نماینده نشده — فرم فعال‌سازی
  if (!status.is_agent) {
    return (
      <div className="p-4 pb-24">
        <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
          → بازگشت
        </button>
        <p className="text-lg font-medium mb-4">🏷 پنل نمایندگی</p>

        {!activation ? (
          <div className="flex flex-col gap-3">
            <p className="text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              با فعال‌سازی نمایندگی، می‌تونی حجم رو با تخفیف عمده بخری و به مشتری‌های خودت بفروشی.
            </p>
            {tiers.map((t) => (
              <div key={t.tier} className="glass-card p-4">
                <p className="font-medium m-0 mb-2">{TIER_LABELS[t.tier] || t.tier}</p>
                <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
                  هزینه فعال‌سازی: {t.activation_fee_toman.toLocaleString("fa-IR")} تومان
                </p>
                <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
                  نرخ خرید هر گیگ: {t.purchase_rate_toman_per_gb.toLocaleString("fa-IR")} تومان
                </p>
                <p className="text-xs m-0 mb-3" style={{ color: "var(--text-secondary)" }}>
                  حداقل موجودی کیف‌پول: {t.min_wallet_balance_toman.toLocaleString("fa-IR")} تومان
                </p>
                <button
                  onClick={() => requestActivation(t.tier)}
                  className="w-full text-sm px-4 py-2 rounded-full"
                  style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
                >
                  درخواست فعال‌سازی
                </button>
              </div>
            ))}
            {error && <p className="text-xs" style={{ color: "var(--danger)" }}>{error}</p>}
          </div>
        ) : (
          <div className="glass-card p-4">
            <p className="text-sm font-medium mb-2">
              درخواست فعال‌سازی رده {TIER_LABELS[activation.tier] || activation.tier} ثبت شد
            </p>
            <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
              مبلغ {activation.activation_fee_toman.toLocaleString("fa-IR")} تومان را به شماره کارت زیر واریز کنید:
            </p>
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm m-0" dir="ltr">💳 {activation.card_number}</p>
              {activation.card_number && <CopyButton text={activation.card_number} />}
            </div>
            <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
              به نام: {activation.card_holder}
            </p>
            {activation.payment_notice && (
              <p className="text-[11px] mb-3" style={{ color: "var(--danger)" }}>
                {activation.payment_notice}
              </p>
            )}
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
          </div>
        )}
      </div>
    );
  }

  // نماینده فعال — پنل مشابه پنل مدیریت ادمین، ولی محدود به داده‌های خودش
  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate(-1)} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-4">🏷 پنل نمایندگی من</p>

      <div className="flex gap-2 mb-4 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="text-xs px-3 py-2 rounded-full"
            style={{
              background: tab === t.key ? "rgba(62,232,195,0.15)" : "var(--surface)",
              color: tab === t.key ? "var(--accent)" : "var(--text-secondary)",
              border: `1px solid ${tab === t.key ? "var(--accent)" : "var(--surface-border)"}`,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "dashboard" && (
        <div className="glass-card p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="font-medium m-0">{TIER_LABELS[status.tier || ""] || status.tier}</p>
            <span
              className="text-[11px] px-2 py-1 rounded-full"
              style={{
                background: status.is_panel_active ? "rgba(62,232,195,0.15)" : "rgba(240,97,106,0.15)",
                color: status.is_panel_active ? "var(--accent)" : "var(--danger)",
              }}
            >
              {status.is_panel_active ? "فعال" : "غیرفعال (موجودی ناکافی)"}
            </span>
          </div>
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            نرخ خرید هر گیگ: {status.purchase_rate_toman_per_gb?.toLocaleString("fa-IR")} تومان
          </p>
          <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
            موجودی کیف‌پول: {status.wallet_balance_toman?.toLocaleString("fa-IR")} تومان
            (حداقل لازم: {status.min_wallet_balance_toman?.toLocaleString("fa-IR")})
          </p>
          <p className="text-xs m-0" style={{ color: "var(--text-secondary)" }}>
            🌐 زیرمجموعه نمایندگی: {status.downline_count} نفر
          </p>
        </div>
      )}

      {tab === "dashboard" && !activation && status.tier && TIER_ORDER[status.tier] < 3 && (
        <div className="glass-card p-4 mt-4">
          <p className="text-sm font-medium mb-3">⬆️ ارتقای رده نمایندگی</p>
          <div className="flex flex-col gap-2">
            {tiers
              .filter((t) => t.tier !== "vip" && TIER_ORDER[t.tier] > TIER_ORDER[status.tier!])
              .map((t) => (
                <button
                  key={t.tier}
                  onClick={() => requestActivation(t.tier)}
                  className="w-full text-sm px-4 py-2 rounded-full text-right"
                  style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
                >
                  ارتقا به {TIER_LABELS[t.tier] || t.tier}
                </button>
              ))}
          </div>
          {error && <p className="text-xs mt-2" style={{ color: "var(--danger)" }}>{error}</p>}
        </div>
      )}

      {tab === "dashboard" && !activation && (
        <div className="glass-card p-4 mt-4">
          <p className="text-sm font-medium mb-2">🛡 سرویس ویژه (مقاوم در برابر فیلترینگ)</p>
          {status.vip_unlocked ? (
            <p className="text-xs m-0" style={{ color: "var(--accent)" }}>
              ✅ فعال — می‌توانید در تب «فروش جدید» سرویس ویژه هم بفروشید.
            </p>
          ) : (
            <>
              <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
                با فعال‌سازی، علاوه بر فروش معمولی (با نرخ فعلی رده‌تان)، می‌توانید سرویس ویژه (مسیر مقاوم رله ایران)
                هم به مشتری‌هاتون بفروشید — فقط حجم ویژه با نرخ جداگانه محاسبه می‌شود، بقیه فروشتان دست‌نخورده می‌ماند.
              </p>
              {tiers
                .filter((t) => t.tier === "vip")
                .map((t) => (
                  <div key={t.tier} className="flex flex-col gap-1 mb-2">
                    <p className="text-xs m-0" style={{ color: "var(--text-secondary)" }}>
                      هزینه فعال‌سازی: {t.activation_fee_toman.toLocaleString("fa-IR")} تومان · نرخ خرید حجم ویژه:{" "}
                      {t.purchase_rate_toman_per_gb.toLocaleString("fa-IR")} تومان/گیگ
                    </p>
                    <button
                      onClick={() => requestActivation("vip")}
                      className="w-full text-sm px-4 py-2 rounded-full"
                      style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
                    >
                      فعال‌سازی سرویس ویژه
                    </button>
                  </div>
                ))}
              {error && <p className="text-xs mt-1" style={{ color: "var(--danger)" }}>{error}</p>}
            </>
          )}
        </div>
      )}

      {tab === "dashboard" && activation && (
        <div className="glass-card p-4 mt-4">
          <p className="text-sm font-medium mb-2">
            {activation.tier === "vip"
              ? "درخواست فعال‌سازی سرویس ویژه ثبت شد"
              : `درخواست ارتقا به رده ${TIER_LABELS[activation.tier] || activation.tier} ثبت شد`}
          </p>
          <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            مبلغ {activation.activation_fee_toman.toLocaleString("fa-IR")} تومان
            {activation.tier !== "vip" && " (مابه‌التفاوت)"} را به شماره کارت زیر واریز کنید:
          </p>
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm m-0" dir="ltr">💳 {activation.card_number}</p>
            {activation.card_number && <CopyButton text={activation.card_number} />}
          </div>
          <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            به نام: {activation.card_holder}
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
        </div>
      )}

      {tab === "sell" && (
        <div className="glass-card p-4">
          <p className="text-sm font-medium mb-3">💸 فروش حجم به مشتری</p>
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>آیدی عددی تلگرام مشتری</label>
          <input
            type="number"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
            dir="ltr"
          />
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>حجم (گیگ)</label>
          <input
            type="number"
            value={volumeGb}
            onChange={(e) => setVolumeGb(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          />
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>قیمت فروش (تومان)</label>
          <input
            type="number"
            value={priceToman}
            onChange={(e) => setPriceToman(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          />
          <label className="text-xs" style={{ color: "var(--text-secondary)" }}>اسم دلخواه سرویس (اختیاری)</label>
          <input
            type="text"
            value={serviceLabel}
            onChange={(e) => setServiceLabel(e.target.value)}
            className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          />
          <label className="flex items-center gap-2 text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            <input type="checkbox" checked={isGiftResale} onChange={(e) => setIsGiftResale(e.target.checked)} />
            این حجم از حجم هدیه رایگان خودم است (بدون کف قیمت)
          </label>
          {status.vip_unlocked && (
            <label className="flex items-center gap-2 text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
              <input type="checkbox" checked={isVipService} onChange={(e) => setIsVipService(e.target.checked)} />
              🛡 این سرویس ویژه است (مسیر مقاوم در برابر فیلترینگ فعال باشد)
            </label>
          )}
          <button
            onClick={submitResale}
            className="w-full text-sm px-4 py-2 rounded-full"
            style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
          >
            ثبت فروش و تحویل سرویس
          </button>
          {resaleError && <p className="text-xs mt-2" style={{ color: "var(--danger)" }}>{resaleError}</p>}
          {resaleResult && <p className="text-xs mt-2" style={{ color: "var(--accent)" }}>{resaleResult}</p>}
        </div>
      )}

      {tab === "customers" && (
        <div className="flex flex-col gap-2">
          {customers.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>هنوز به کسی نفروخته‌اید.</p>
          ) : (
            customers.map((c) => (
              <div key={c.id} className="glass-card p-3">
                <p className="text-sm font-medium m-0 mb-1">
                  {c.full_name || "-"} {c.telegram_username && `(@${c.telegram_username})`}
                </p>
                <p className="text-xs m-0" style={{ color: "var(--text-secondary)" }}>
                  {c.volume_gb}گیگ · {c.price_toman.toLocaleString("fa-IR")}ت {c.is_gift_resale && "· هدیه"} ·{" "}
                  {new Date(c.purchased_at).toLocaleDateString("fa-IR")}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "downline" && (
        <div className="flex flex-col gap-2">
          {!status.downline || status.downline.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>هنوز نماینده‌ای زیرمجموعه شما نیست.</p>
          ) : (
            status.downline.map((d) => (
              <div key={d.agent_id} className="glass-card p-3 flex items-center justify-between">
                <span className="text-sm">{TIER_LABELS[d.tier] || d.tier}</span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>سطح {d.level}</span>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "link" && (
        <div className="glass-card p-4">
          <p className="text-sm font-medium mb-2">🔗 لینک اختصاصی دعوت مشتری</p>
          <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
            مشتری‌هایی که از این لینک وارد بشن، دائمی به شما متصل می‌مونن و می‌تونن با قیمت اختصاصی شما خرید کنن —
            همون ربات و اپ NovaTunnel، بدون هیچ تغییری در برند.
          </p>

          {status.agent_slug ? (
            <>
              <p className="text-xs p-2 rounded-lg mb-3" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--surface-border)" }} dir="ltr">
                {agentLink}
              </p>
              <div className="flex gap-2">
                <button onClick={copyLink} className="flex-1 text-sm px-4 py-2 rounded-full" style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}>
                  {slugCopied ? "کپی شد ✅" : "📋 کپی لینک"}
                </button>
                <button onClick={shareLink} className="flex-1 text-sm px-4 py-2 rounded-full" style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}>
                  📤 اشتراک‌گذاری
                </button>
              </div>
            </>
          ) : (
            <>
              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
                یک شناسه کوتاه انگلیسی انتخاب کن (فقط حروف کوچک، عدد، خط تیره)
              </label>
              <input
                type="text"
                value={slugInput}
                onChange={(e) => setSlugInput(e.target.value)}
                placeholder="مثلاً: ali-vpn"
                className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
                dir="ltr"
              />
              <button onClick={saveSlug} className="w-full text-sm px-4 py-2 rounded-full" style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}>
                ثبت شناسه و ساخت لینک
              </button>
              {slugError && <p className="text-xs mt-2" style={{ color: "var(--danger)" }}>{slugError}</p>}
            </>
          )}
        </div>
      )}

      {tab === "pricing" && (
        <div className="flex flex-col gap-3">
          <p className="text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
            قیمتی که برای مشتری‌های متصل به شما نمایش داده می‌شود. باید حداقل برابر هزینه خرید شما باشد.
          </p>
          {pricing.map((p) => (
            <div key={p.package_id} className="glass-card p-4">
              <p className="text-sm font-medium m-0 mb-1">{p.name} ({p.volume_gb}گیگ)</p>
              <p className="text-xs m-0 mb-2" style={{ color: "var(--text-secondary)" }}>
                قیمت پیش‌فرض: {p.default_price_toman.toLocaleString("fa-IR")}ت
                {p.agent_price_toman !== null && ` · قیمت فعلی شما: ${p.agent_price_toman.toLocaleString("fa-IR")}ت`}
              </p>
              <div className="flex gap-2">
                <input
                  type="number"
                  defaultValue={p.agent_price_toman ?? p.default_price_toman}
                  onChange={(e) => setPriceEdits((prev) => ({ ...prev, [p.package_id]: e.target.value }))}
                  className="flex-1 glass-card px-3 py-2 text-sm bg-transparent outline-none"
                />
                <button
                  onClick={() => savePrice(p.package_id)}
                  className="text-xs px-4 py-2 rounded-full"
                  style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
                >
                  ذخیره
                </button>
              </div>
              {priceSaved[p.package_id] && (
                <p className="text-[11px] mt-1" style={{ color: priceSaved[p.package_id].startsWith("✅") ? "var(--accent)" : "var(--danger)" }}>
                  {priceSaved[p.package_id]}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === "cards" && (
        <div className="flex flex-col gap-3">
          <p className="text-xs mb-1" style={{ color: "var(--text-secondary)" }}>
            وقتی مشتری از طریق لینک اختصاصی شما خرید می‌کند، دقیقاً یکی از همین کارت‌ها به او نمایش داده می‌شود و
            رسید هم مستقیم برای تایید خودتان ارسال می‌شود — نه ادمین.
          </p>

          <div className="glass-card p-4">
            <p className="text-sm font-medium mb-3">➕ افزودن کارت جدید</p>
            <label className="text-xs" style={{ color: "var(--text-secondary)" }}>شماره کارت</label>
            <input
              type="text"
              value={newCardNumber}
              onChange={(e) => setNewCardNumber(e.target.value)}
              placeholder="6219-8614-0039-0828"
              className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
              dir="ltr"
            />
            <label className="text-xs" style={{ color: "var(--text-secondary)" }}>به نام</label>
            <input
              type="text"
              value={newCardHolder}
              onChange={(e) => setNewCardHolder(e.target.value)}
              className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
            />
            {cardError && <p className="text-[11px] mb-2" style={{ color: "var(--danger)" }}>{cardError}</p>}
            <button
              onClick={addCard}
              className="w-full text-sm px-4 py-2 rounded-full"
              style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
            >
              افزودن کارت
            </button>
          </div>

          {cards.length === 0 ? (
            <p className="text-xs text-center py-4" style={{ color: "var(--text-secondary)" }}>
              هنوز کارتی ثبت نکرده‌اید — تا کارتی فعال نداشته باشید، مشتری‌های لینک اختصاصی شما کارت مالک سیستم
              را می‌بینند.
            </p>
          ) : (
            cards.map((c) => (
              <div key={c.id} className="glass-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span
                    className="text-[11px] px-2 py-1 rounded-full"
                    style={{
                      background: c.is_active ? "rgba(62,232,195,0.15)" : "rgba(255,255,255,0.06)",
                      color: c.is_active ? "var(--accent)" : "var(--text-secondary)",
                    }}
                  >
                    {c.is_active ? "فعال" : "غیرفعال"}
                  </span>
                  <button onClick={() => removeCard(c.id)} className="text-xs" style={{ color: "var(--danger)" }}>
                    حذف
                  </button>
                </div>
                <p className="text-sm m-0 mb-1" dir="ltr">{c.card_number}</p>
                <p className="text-xs m-0 mb-3" style={{ color: "var(--text-secondary)" }}>{c.card_holder}</p>
                <button
                  onClick={() => toggleCardActive(c)}
                  className="w-full text-xs px-4 py-2 rounded-full"
                  style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
                >
                  {c.is_active ? "غیرفعال کن" : "فعال کن"}
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "accounting" && (
        !accounting ? (
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>در حال بارگذاری...</p>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="glass-card p-4">
              <p className="text-sm font-medium mb-3">📊 فروش من</p>
              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: "امروز", count: accounting.sales.today_count, amount: accounting.sales.today_sales },
                  { label: "این هفته", count: accounting.sales.week_count, amount: accounting.sales.week_sales },
                  { label: "این ماه", count: accounting.sales.month_count, amount: accounting.sales.month_sales },
                ].map((s) => (
                  <div key={s.label}>
                    <p className="text-[11px] m-0 mb-1" style={{ color: "var(--text-secondary)" }}>{s.label}</p>
                    <p className="text-sm font-medium m-0" style={{ color: "var(--accent)" }}>
                      {s.count.toLocaleString("fa-IR")} فروش
                    </p>
                    <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>
                      {s.amount.toLocaleString("fa-IR")}ت
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card p-4">
              <p className="text-sm font-medium mb-3">🛒 هزینه خرید حجم (از کیف‌پول)</p>
              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: "امروز", amount: accounting.cost.today_cost },
                  { label: "این هفته", amount: accounting.cost.week_cost },
                  { label: "این ماه", amount: accounting.cost.month_cost },
                ].map((c) => (
                  <div key={c.label}>
                    <p className="text-[11px] m-0 mb-1" style={{ color: "var(--text-secondary)" }}>{c.label}</p>
                    <p className="text-sm font-medium m-0" style={{ color: "var(--accent-violet)" }}>
                      {c.amount.toLocaleString("fa-IR")}ت
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card p-4">
              <p className="text-sm font-medium mb-3">💼 سود خالص (کل دوره)</p>
              <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
                فروش کل: {accounting.sales.total_sales.toLocaleString("fa-IR")}ت
              </p>
              <p className="text-xs m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
                هزینه خرید حجم: {accounting.cost.total_cost.toLocaleString("fa-IR")}ت
              </p>
              <p className="text-xs m-0 mb-2" style={{ color: "var(--text-secondary)" }}>
                هزینه‌های ثبت‌شده: {accounting.expense_total.toLocaleString("fa-IR")}ت
              </p>
              <p
                className="text-lg font-medium m-0"
                style={{ color: accounting.net_profit >= 0 ? "var(--accent)" : "var(--danger)" }}
              >
                {accounting.net_profit.toLocaleString("fa-IR")} تومان
              </p>
            </div>

            <div className="glass-card p-4">
              <p className="text-sm font-medium mb-3">➕ ثبت هزینه</p>
              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>مبلغ (تومان)</label>
              <input
                type="number"
                value={expenseAmount}
                onChange={(e) => setExpenseAmount(e.target.value)}
                className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
              />
              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>توضیح</label>
              <input
                type="text"
                value={expenseDesc}
                onChange={(e) => setExpenseDesc(e.target.value)}
                className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
              />
              <label className="text-xs" style={{ color: "var(--text-secondary)" }}>دسته‌بندی</label>
              <select
                value={expenseCategory}
                onChange={(e) => setExpenseCategory(e.target.value)}
                className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
              >
                {EXPENSE_CATEGORIES.map((c) => (
                  <option key={c} value={c} style={{ background: "var(--bg)" }}>{c}</option>
                ))}
              </select>
              <button
                onClick={addExpense}
                className="w-full text-sm px-4 py-2 rounded-full"
                style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
              >
                ثبت هزینه
              </button>
              {expenseError && <p className="text-xs mt-2" style={{ color: "var(--danger)" }}>{expenseError}</p>}
            </div>

            <p className="font-medium m-0">تاریخچه هزینه‌ها</p>
            {accounting.expenses.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>هنوز هزینه‌ای ثبت نشده.</p>
            ) : (
              accounting.expenses.map((e) => (
                <div key={e.id} className="glass-card p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm m-0 mb-1">{e.description}</p>
                    <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>
                      {e.category && `${e.category} · `}
                      {new Date(e.created_at).toLocaleDateString("fa-IR")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-sm" style={{ color: "var(--danger)" }}>
                      {e.amount_toman.toLocaleString("fa-IR")}ت
                    </span>
                    <button onClick={() => removeExpense(e.id)} className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      حذف
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )
      )}
    </div>
  );
}
