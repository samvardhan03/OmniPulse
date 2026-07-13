"use client";

import { motion } from "framer-motion";

interface HnswLaneProps {
  active: boolean;
  insertCount: number;
}

export default function HnswLane({ active, insertCount }: HnswLaneProps) {
  const nodes = Array.from({ length: Math.min(insertCount + 1, 6) }, (_, i) => i);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
          HNSW index (SW1 metric)
        </span>
      </div>
      <motion.div
        className="p-4 border flex gap-6 items-start"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
        animate={{ opacity: active ? 1 : 0.4 }}
        transition={{ duration: 0.3 }}
      >
        <div className="font-mono text-[12px] flex-1" style={{ color: "var(--ink)" }}>
          <span style={{ color: "var(--accent)" }}>{"ConcurrentHnsw"}</span>
          <span>{"<PointCloud, SlicedWasserstein>"}</span>
          {"\n"}
          <span style={{ color: "var(--ink-mute)" }}>{`  .insert(fp, id)  // node ${insertCount}`}</span>
          {"\n"}
          <span style={{ color: "var(--ink-mute)" }}>{"  // SW₁ distance < 1e-6 → nearest neighbour"}</span>
        </div>

        <div className="relative flex items-center gap-2 flex-wrap max-w-[160px]">
          {nodes.map((i) => (
            <motion.div
              key={i}
              className="w-6 h-6 rounded-full border flex items-center justify-center"
              style={{
                borderColor: "var(--accent)",
                backgroundColor: i === insertCount ? "var(--accent)" : "transparent",
              }}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.08 }}
            >
              <span className="font-mono text-[9px]" style={{ color: i === insertCount ? "var(--bg)" : "var(--accent)" }}>
                {i}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
