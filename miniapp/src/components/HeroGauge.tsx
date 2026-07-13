import { motion } from "framer-motion";

interface Props {
  remainingGb: number;
  totalGb: number;
  label: string;
}

const SIZE = 260;
const STROKE = 16;
const R = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * R;
const HALF = CIRCUMFERENCE / 2;

export default function HeroGauge({ remainingGb, totalGb, label }: Props) {
  const percent = totalGb > 0 ? Math.max(0, Math.min(100, (remainingGb / totalGb) * 100)) : 0;
  const fillLength = (percent / 100) * HALF;
  const cx = SIZE / 2;
  const cy = SIZE / 2;

  const color = percent > 40 ? "#3ee8c3" : percent > 15 ? "#f0c419" : "#f0616a";

  return (
    <div className="flex flex-col items-center">
      <svg width={SIZE} height={SIZE * 0.62} viewBox={`0 0 ${SIZE} ${SIZE * 0.62}`}>
        <g transform={`rotate(180 ${cx} ${cy})`}>
          <circle
            cx={cx}
            cy={cy}
            r={R}
            fill="none"
            stroke="rgba(70,220,190,0.12)"
            strokeWidth={STROKE}
            strokeDasharray={`${HALF} ${HALF}`}
            strokeLinecap="round"
          />
          <motion.circle
            cx={cx}
            cy={cy}
            r={R}
            fill="none"
            stroke={color}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={`${HALF} ${HALF}`}
            initial={{ strokeDashoffset: HALF }}
            animate={{ strokeDashoffset: HALF - fillLength }}
            transition={{ duration: 1, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 6px ${color}90)` }}
          />
        </g>
        {/* خط‌های درجه‌بندی مثل کیلومترشمار ماشین */}
        {Array.from({ length: 9 }).map((_, i) => {
          const angle = 180 + (i / 8) * 180;
          const rad = (angle * Math.PI) / 180;
          const inner = R - STROKE / 2 - 4;
          const outer = R - STROKE / 2 - 12;
          const x1 = cx + inner * Math.cos(rad);
          const y1 = cy + inner * Math.sin(rad);
          const x2 = cx + outer * Math.cos(rad);
          const y2 = cy + outer * Math.sin(rad);
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="rgba(127,168,156,0.35)"
              strokeWidth={2}
            />
          );
        })}
      </svg>

      <div className="-mt-6 flex flex-col items-center">
        <motion.p
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-5xl font-bold m-0"
          style={{ color }}
        >
          {remainingGb.toFixed(1)}
        </motion.p>
        <p className="text-sm m-0 mt-1" style={{ color: "var(--text-secondary)" }}>
          گیگابایت باقی‌مانده
        </p>
        <p className="text-xs m-0 mt-2 px-3 py-1 rounded-full" style={{ background: "rgba(127,168,156,0.12)", color: "var(--text-secondary)" }}>
          {label}
        </p>
      </div>
    </div>
  );
}
