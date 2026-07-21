import { NavLink } from "react-router-dom";

interface NavItem {
  label: string;
  to?: string;
  comingSoon?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV: NavGroup[] = [
  { label: "نمای کلی", items: [{ label: "داشبورد", to: "/" }] },
  {
    label: "فروش",
    items: [
      { label: "مشتریان", to: "/customers" },
      { label: "نمایندگان", comingSoon: true },
      { label: "بسته‌ها", comingSoon: true },
      { label: "سفارش‌ها و رسیدها", comingSoon: true },
    ],
  },
  {
    label: "مالی",
    items: [
      { label: "حسابداری", comingSoon: true },
      { label: "شارژ کیف‌پول", comingSoon: true },
      { label: "کارت‌های پرداخت", comingSoon: true },
    ],
  },
  {
    label: "سیستم",
    items: [
      { label: "پیام همگانی", comingSoon: true },
      { label: "تنظیمات", comingSoon: true },
    ],
  },
];

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <aside className="w-[264px] shrink-0 h-full border-l border-[var(--surface-border)] bg-[rgba(5,9,20,0.5)] flex flex-col">
      <div className="px-5 py-6 border-b border-[var(--surface-border)]">
        <div className="text-lg font-bold text-[var(--accent)]">NovaTunnel</div>
        <div className="text-xs text-[var(--text-secondary)]">پنل مدیریت</div>
      </div>
      <nav className="flex-1 overflow-y-auto scrollbar-thin py-4 px-3">
        {NAV.map((group) => (
          <div key={group.label} className="mb-5">
            <div className="text-[11px] uppercase tracking-wide text-[var(--text-secondary)] px-3 mb-2">
              {group.label}
            </div>
            <div className="flex flex-col gap-1">
              {group.items.map((item) =>
                item.to ? (
                  <NavLink
                    key={item.label}
                    to={item.to}
                    onClick={onNavigate}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      `px-3 py-2 rounded-lg text-sm transition-colors ${
                        isActive
                          ? "bg-[rgba(62,232,195,0.12)] text-[var(--accent)] font-semibold"
                          : "text-[var(--text-primary)] hover:bg-[rgba(255,255,255,0.04)]"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ) : (
                  <div
                    key={item.label}
                    className="px-3 py-2 rounded-lg text-sm text-[var(--text-secondary)] flex items-center justify-between cursor-not-allowed"
                  >
                    <span>{item.label}</span>
                    <span className="badge info !text-[10px] !py-0.5">به‌زودی</span>
                  </div>
                ),
              )}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
