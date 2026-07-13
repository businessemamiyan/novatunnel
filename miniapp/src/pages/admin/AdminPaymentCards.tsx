import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api";
import { PaymentCard } from "../../types";

export default function AdminPaymentCards() {
  const [cards, setCards] = useState<PaymentCard[]>([]);
  const [newNumber, setNewNumber] = useState("");
  const [newHolder, setNewHolder] = useState("");
  const [edits, setEdits] = useState<Record<number, { card_number?: string; card_holder?: string }>>({});
  const [savedId, setSavedId] = useState<number | null>(null);
  const [addError, setAddError] = useState("");
  const navigate = useNavigate();

  const load = () => api.get<PaymentCard[]>("/payment-cards").then(setCards);
  useEffect(() => {
    load();
  }, []);

  const addCard = async () => {
    setAddError("");
    if (!newNumber.trim() || !newHolder.trim()) {
      setAddError("لطفاً هم شماره کارت و هم نام صاحب کارت را وارد کنید.");
      return;
    }
    try {
      await api.post("/payment-cards", { card_number: newNumber.trim(), card_holder: newHolder.trim() });
      setNewNumber("");
      setNewHolder("");
      load();
    } catch (e) {
      setAddError(e instanceof Error ? e.message : "خطا در افزودن کارت");
    }
  };

  const setField = (id: number, field: "card_number" | "card_holder", value: string) => {
    setEdits((prev) => ({ ...prev, [id]: { ...prev[id], [field]: value } }));
  };

  const save = async (c: PaymentCard) => {
    const e = edits[c.id] || {};
    await api.patch(`/payment-cards/${c.id}`, {
      card_number: e.card_number ?? c.card_number,
      card_holder: e.card_holder ?? c.card_holder,
      is_active: c.is_active,
    });
    setSavedId(c.id);
    setTimeout(() => setSavedId(null), 1200);
    load();
  };

  const toggleActive = async (c: PaymentCard) => {
    await api.patch(`/payment-cards/${c.id}`, {
      card_number: c.card_number,
      card_holder: c.card_holder,
      is_active: !c.is_active,
    });
    load();
  };

  const remove = async (id: number) => {
    await api.delete(`/payment-cards/${id}`);
    load();
  };

  return (
    <div className="p-4 pb-24">
      <button onClick={() => navigate("/admin")} className="text-sm mb-4" style={{ color: "var(--accent)" }}>
        → بازگشت
      </button>
      <p className="text-lg font-medium mb-1">💳 شماره کارت‌های دریافت پرداخت</p>
      <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
        هنگام پرداخت، یکی از کارت‌های فعال به‌صورت تصادفی به مشتری نمایش داده می‌شود.
      </p>

      <div className="glass-card p-4 mb-4">
        <p className="text-sm font-medium mb-3">➕ افزودن کارت جدید</p>
        <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
          شماره کارت
        </label>
        <input
          type="text"
          value={newNumber}
          onChange={(e) => setNewNumber(e.target.value)}
          placeholder="6219-8614-0039-0828"
          className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
          dir="ltr"
        />
        <label className="text-xs" style={{ color: "var(--text-secondary)" }}>
          به نام
        </label>
        <input
          type="text"
          value={newHolder}
          onChange={(e) => setNewHolder(e.target.value)}
          placeholder="حسن امامیان"
          className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3 mt-1"
        />
        {addError && (
          <p className="text-[11px] mb-2" style={{ color: "var(--danger)" }}>
            {addError}
          </p>
        )}
        <button
          onClick={addCard}
          className="w-full text-sm px-4 py-2 rounded-full"
          style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
        >
          افزودن کارت
        </button>
      </div>

      <div className="flex flex-col gap-3">
        {cards.map((c) => (
          <div key={c.id} className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <span
                className="text-[11px] px-2 py-1 rounded-full"
                style={{
                  background: c.is_active ? "rgba(62,232,195,0.15)" : "rgba(255,255,255,0.06)",
                  color: c.is_active ? "var(--accent)" : "var(--text-secondary)",
                }}
              >
                {c.is_active ? "فعال" : "غیرفعال"}
              </span>
              <button onClick={() => remove(c.id)} className="text-xs" style={{ color: "var(--danger)" }}>
                حذف
              </button>
            </div>

            <input
              type="text"
              defaultValue={c.card_number}
              onChange={(e) => setField(c.id, "card_number", e.target.value)}
              className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-2"
              dir="ltr"
            />
            <input
              type="text"
              defaultValue={c.card_holder}
              onChange={(e) => setField(c.id, "card_holder", e.target.value)}
              className="w-full glass-card px-3 py-2 text-sm bg-transparent outline-none mb-3"
            />

            <div className="flex gap-2">
              <button
                onClick={() => save(c)}
                className="flex-1 text-xs px-4 py-2 rounded-full"
                style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
              >
                {savedId === c.id ? "ذخیره شد ✅" : "ذخیره"}
              </button>
              <button
                onClick={() => toggleActive(c)}
                className="flex-1 text-xs px-4 py-2 rounded-full"
                style={{ background: "rgba(155,107,214,0.15)", color: "var(--accent-violet)" }}
              >
                {c.is_active ? "غیرفعال کن" : "فعال کن"}
              </button>
            </div>
          </div>
        ))}
        {cards.length === 0 && (
          <p className="text-xs text-center py-4" style={{ color: "var(--text-secondary)" }}>
            هنوز کارتی ثبت نشده. یک کارت اضافه کنید تا در فرآیند پرداخت نمایش داده شود.
          </p>
        )}
      </div>
    </div>
  );
}
