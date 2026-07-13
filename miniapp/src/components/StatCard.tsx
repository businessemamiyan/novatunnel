import { motion } from "framer-motion";

interface Props {
  label: string;
  value: string;
  accent?: "teal" | "violet";
}

export default function StatCard({ label, value, accent = "teal" }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="glass-card p-4 flex-1 min-w-[120px]"
    >
      <p className="text-[11px] m-0 mb-1" style={{ color: "var(--text-secondary)" }}>
        {label}
      </p>
      <p
        className="text-xl font-medium m-0"
        style={{ color: accent === "teal" ? "var(--accent)" : "var(--accent-violet)" }}
      >
        {value}
      </p>
    </motion.div>
  );
}
