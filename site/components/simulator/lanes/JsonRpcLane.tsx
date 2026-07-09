"use client";

import { motion } from "framer-motion";

interface JsonRpcLaneProps {
  active: boolean;
  envelope: object | null;
}

export default function JsonRpcLane({ active, envelope }: JsonRpcLaneProps) {
  const text = envelope
    ? JSON.stringify(envelope, null, 2)
    : `{
  "jsonrpc": "2.0",
  "id": "01J4...",
  "method": "tools/call",
  "params": {
    "name": "generate_fingerprint",
    "arguments": { ... }
  }
}`;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
          Stdio JSON-RPC envelope
        </span>
      </div>
      <motion.div
        className="p-4 border overflow-auto max-h-[180px]"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
        animate={{ opacity: active ? 1 : 0.4 }}
        transition={{ duration: 0.3 }}
      >
        <pre className="font-mono text-[12px] whitespace-pre-wrap" style={{ color: "var(--ink)" }}>
          {text}
        </pre>
      </motion.div>
    </div>
  );
}
