"use client";

import { motion } from "framer-motion";

export default function RustLane({ active }: { active: boolean }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
          Rust orchestrator
        </span>
      </div>
      <motion.div
        className="p-4 border font-mono text-[12px]"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
        animate={{ opacity: active ? 1 : 0.4 }}
        transition={{ duration: 0.3 }}
      >
        <span style={{ color: "var(--ink-mute)" }}>{"// server.rs:162-211 - generate_fingerprint handler"}</span>
        {"\n"}
        <span style={{ color: "var(--accent)" }}>{"let signal"}</span>
        <span style={{ color: "var(--ink)" }}>{" = shm::read_and_unlink(&req.media_shm_name, n * 4)?;"}</span>
        {"\n"}
        <span style={{ color: "var(--accent)" }}>{"let fp"}</span>
        <span style={{ color: "var(--ink)" }}>{" = tokio::task::spawn_blocking(move || {"}</span>
        {"\n"}
        <span style={{ color: "var(--ink)" }}>{"    kernel.run(&signal, &cfg)"}</span>
        {"\n"}
        <span style={{ color: "var(--ink)" }}>{"}).await??;"}</span>
      </motion.div>
    </div>
  );
}
