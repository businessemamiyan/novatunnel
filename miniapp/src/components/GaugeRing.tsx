interface Props {
  percent: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
}

export default function GaugeRing({ percent, size = 64, strokeWidth = 6, label, sublabel }: Props) {
  const clamped = Math.max(0, Math.min(100, percent));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);
  const center = size / 2;

  return (
    <div className="flex items-center gap-3">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="rgba(70,220,190,0.15)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#3ee8c3"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${center} ${center})`}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      {(label || sublabel) && (
        <div className="text-center">
          {label && <p className="text-base font-medium m-0">{label}</p>}
          {sublabel && <p className="text-[11px] m-0" style={{ color: "var(--text-secondary)" }}>{sublabel}</p>}
        </div>
      )}
    </div>
  );
}
