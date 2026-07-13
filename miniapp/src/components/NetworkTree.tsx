import { motion } from "framer-motion";
import { NetworkPerson } from "../types";

interface Props {
  level: number;
  people: NetworkPerson[];
}

const levelColor: Record<number, string> = {
  1: "#3ee8c3",
  2: "#7fd8c9",
  3: "#9b6bd6",
};

export default function NetworkTree({ level, people }: Props) {
  const color = levelColor[level] ?? "#7fa89c";

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        <span
          className="w-2 h-2 rounded-full"
          style={{ background: color, boxShadow: `0 0 8px ${color}` }}
        />
        <p className="text-sm font-medium m-0" style={{ color }}>
          سطح {level} — {people.length} نفر
        </p>
      </div>
      {people.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          هنوز کسی در این سطح نیست.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          {people.map((p, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: i * 0.03 }}
              className="glass-card px-3 py-2 flex items-center gap-2"
              style={{ borderColor: `${color}40` }}
            >
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                style={{ background: `${color}25`, color }}
              >
                {(p.name || "?").trim().charAt(0)}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium m-0 truncate">{p.name ?? "کاربر"}</p>
                <p className="text-[10px] m-0" style={{ color: "var(--text-secondary)" }}>
                  {p.verified ? "✅ احراز شده" : "⚠️ احراز نشده"}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
