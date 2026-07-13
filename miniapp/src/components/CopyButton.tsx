import { useState } from "react";

import { haptic } from "../telegram";

export default function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    haptic("light");
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      onClick={copy}
      className="text-[11px] px-2 py-1 rounded-full shrink-0"
      style={{ background: "rgba(62,232,195,0.15)", color: "var(--accent)" }}
    >
      {copied ? "کپی شد ✅" : "📋 کپی"}
    </button>
  );
}
