import { motion } from "framer-motion";
import { ServiceSummary } from "../types";
import GaugeRing from "./GaugeRing";

interface Props {
  service: ServiceSummary;
  onClick?: () => void;
  index?: number;
}

function statusColor(status: string): string {
  if (status.includes("🟢")) return "#3ee8c3";
  if (status.includes("🟡")) return "#f0c419";
  return "#f0616a";
}

export default function ServiceCard({ service, onClick, index = 0 }: Props) {
  const remaining = Math.max(service.traffic_limit_gb - service.traffic_used_gb, 0);
  const percentRemaining =
    service.traffic_limit_gb > 0 ? (remaining / service.traffic_limit_gb) * 100 : 0;

  return (
    <motion.button
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.05 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="glass-card p-4 w-full text-right flex items-center justify-between gap-3"
    >
      <div className="flex-1 min-w-0">
        <p className="font-medium m-0 mb-1 truncate">{service.label}</p>
        <span
          className="inline-block text-[11px] px-2 py-0.5 rounded-full"
          style={{
            color: statusColor(service.status),
            background: `${statusColor(service.status)}22`,
          }}
        >
          {service.status}
        </span>
      </div>
      <GaugeRing
        percent={percentRemaining}
        size={52}
        strokeWidth={5}
        label={`${remaining.toFixed(1)}`}
        sublabel="گیگ باقی"
      />
    </motion.button>
  );
}
