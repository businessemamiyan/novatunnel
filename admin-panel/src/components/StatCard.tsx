interface StatCardProps {
  label: string;
  value: string;
  trend?: string;
  trendDown?: boolean;
}

export default function StatCard({ label, value, trend, trendDown }: StatCardProps) {
  return (
    <article className="card">
      <span className="stat-label">{label}</span>
      <p className="stat-value">{value}</p>
      {trend && <span className={`trend ${trendDown ? "down" : ""}`}>{trend}</span>}
    </article>
  );
}
