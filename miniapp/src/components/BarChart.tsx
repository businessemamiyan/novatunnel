import { motion } from "framer-motion";

interface Props {
  data: { label: string; value: number }[];
}

export default function BarChart({ data }: Props) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="flex items-end gap-2 h-32">
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${Math.max((d.value / max) * 100, 3)}%` }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
            className="w-full rounded-t-md"
            style={{ background: "linear-gradient(180deg, #3ee8c3, #9b6bd6)" }}
          />
          <span className="text-[10px]" style={{ color: "var(--text-secondary)" }}>
            {d.label}
          </span>
        </div>
      ))}
    </div>
  );
}
