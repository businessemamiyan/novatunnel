import { useAuth } from "../auth/AuthContext";

export default function Header({
  title,
  subtitle,
  onMenuClick,
}: {
  title: string;
  subtitle?: string;
  onMenuClick?: () => void;
}) {
  const { admin, logout } = useAuth();

  return (
    <header className="flex items-center justify-between gap-4 px-6 py-4 border-b border-[var(--surface-border)]">
      <div className="flex items-center gap-3">
        <button
          className="md:hidden btn btn-secondary !p-2"
          onClick={onMenuClick}
          aria-label="باز کردن منو"
        >
          ☰
        </button>
        <div>
          <h1 className="text-lg font-bold">{title}</h1>
          {subtitle && <p className="text-xs text-[var(--text-secondary)]">{subtitle}</p>}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {admin && (
          <span className="text-xs text-[var(--text-secondary)]">
            ادمین <span className="text-[var(--text-primary)]">#{admin.telegram_id}</span>
          </span>
        )}
        <button className="btn btn-secondary" onClick={() => logout()}>
          خروج
        </button>
      </div>
    </header>
  );
}
