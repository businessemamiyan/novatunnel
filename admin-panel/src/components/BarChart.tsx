interface BarChartPoint {
  label: string;
  value: number;
  title?: string;
}

export default function BarChart({ points }: { points: BarChartPoint[] }) {
  const max = Math.max(...points.map((p) => p.value), 1);
  return (
    <div>
      <div className="chart-bar-row">
        {points.map((p) => (
          <div key={p.label} className="flex-1 flex flex-col justify-end h-full" title={p.title}>
            <div className="chart-bar" style={{ height: `${Math.max((p.value / max) * 100, 2)}%` }} />
          </div>
        ))}
      </div>
      <div className="flex gap-[10px]">
        {points.map((p) => (
          <div key={p.label} className="flex-1 chart-bar-label">
            {p.label}
          </div>
        ))}
      </div>
    </div>
  );
}
