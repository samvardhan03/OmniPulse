"use client";

import { motion } from "framer-motion";

export default function FfiBridgeLane({ active }: { active: boolean }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
          cxx FFI bridge
        </span>
      </div>
      <motion.div
        className="p-4 border font-mono text-[12px]"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
        animate={{ opacity: active ? 1 : 0.4 }}
        transition={{ duration: 0.3 }}
      >
        <span style={{ color: "var(--ink-mute)" }}>{"// omni_ffi_kernel.rs:90-97"}</span>
        {"\n"}
        <span style={{ color: "var(--accent)" }}>{"unsafe fn"}</span>
        <span style={{ color: "var(--ink)" }}>{" run_wst_pipeline("}</span>
        {"\n"}
        <span style={{ color: "var(--ink)" }}>{"    ptr: u64, len: u32,"}</span>
        {"\n"}
        <span style={{ color: "var(--ink)" }}>{"    j: u32, q: u32, depth: u32"}</span>
        {"\n"}
        <span style={{ color: "var(--ink)" }}>{") → WSTResult"}</span>
        {"\n"}
        <span style={{ color: "var(--ink-mute)" }}>{"// → omni_ffi::execute_fingerprint_pass(...)"}</span>
      </motion.div>
    </div>
  );
}
