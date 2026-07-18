"use client";

import { motion } from "framer-motion";

interface KernelLaneProps {
  active: boolean;
  useGpu: boolean;
  onToggle: () => void;
}

export default function KernelLane({ active, useGpu, onToggle }: KernelLaneProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
            C++/CUDA kernel
          </span>
        </div>
        <button
          onClick={onToggle}
          className="font-mono text-[11px] uppercase tracking-[0.1em] px-3 py-1 border transition-opacity hover:opacity-70"
          style={{
            borderColor: "var(--rule)",
            color: useGpu ? "var(--accent)" : "var(--ink-mute)",
            backgroundColor: "var(--bg-elev)",
          }}
        >
          {useGpu ? "CUDA Hopper" : "CPU Morlet"}
        </button>
      </div>
      <motion.div
        className="p-4 border font-mono text-[12px]"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
        animate={{ opacity: active ? 1 : 0.4 }}
        transition={{ duration: 0.3 }}
      >
        {useGpu ? (
          <>
            <span style={{ color: "var(--ink-mute)" }}>{"// CUDA Hopper - wst_bridge_cuda.cpp"}</span>
            {"\n"}
            <span style={{ color: "var(--accent)" }}>{"WSTEngine"}</span>
            <span style={{ color: "var(--ink)" }}>{"<HopperTag, /*J=*/8, /*Q=*/16> engine;"}</span>
            {"\n"}
            <span style={{ color: "var(--ink)" }}>{"engine.forward(ptr, len);  // GPU kernel launch"}</span>
          </>
        ) : (
          <>
            <span style={{ color: "var(--ink-mute)" }}>{"// CPU Morlet fallback - wst_bridge_cpu.cpp"}</span>
            {"\n"}
            <span style={{ color: "var(--accent)" }}>{"AnalyticMorletBank"}</span>
            <span style={{ color: "var(--ink)" }}>{"<8, 16> bank;"}</span>
            {"\n"}
            <span style={{ color: "var(--ink)" }}>{"bank.scatter_radix2(ptr, len);  // Radix-2 FFT"}</span>
          </>
        )}
        {"\n"}
        <span style={{ color: "var(--ink-mute)" }}>
          {`# build: cargo build -p omnipulse-mcp --features ${useGpu ? "cuda --release" : "omni-ffi"}`}
        </span>
      </motion.div>
    </div>
  );
}
