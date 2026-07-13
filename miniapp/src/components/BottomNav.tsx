import { NavLink } from "react-router-dom";

interface Props {
  isAdmin: boolean;
}

const itemClass = ({ isActive }: { isActive: boolean }) =>
  `flex flex-col items-center gap-1 py-2 flex-1 text-xs transition-colors ${
    isActive ? "text-tealglow" : "text-[var(--text-secondary)]"
  }`;

export default function BottomNav({ isAdmin }: Props) {
  return (
    <nav
      className="fixed bottom-0 inset-x-0 flex glass-card rounded-b-none border-b-0"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <NavLink to="/" end className={itemClass}>
        <span>🏠</span>
        <span>خانه</span>
      </NavLink>
      <NavLink to="/purchase" className={itemClass}>
        <span>🛒</span>
        <span>خرید</span>
      </NavLink>
      <NavLink to="/services" className={itemClass}>
        <span>🧩</span>
        <span>سرویس‌ها</span>
      </NavLink>
      <NavLink to="/network" className={itemClass}>
        <span>🌐</span>
        <span>شبکه من</span>
      </NavLink>
      <NavLink to="/wallet" className={itemClass}>
        <span>👛</span>
        <span>کیف پول</span>
      </NavLink>
      <NavLink to="/support" className={itemClass}>
        <span>🎫</span>
        <span>پشتیبانی</span>
      </NavLink>
      {isAdmin && (
        <NavLink to="/admin" className={itemClass}>
          <span>🛠</span>
          <span>مدیریت</span>
        </NavLink>
      )}
    </nav>
  );
}
