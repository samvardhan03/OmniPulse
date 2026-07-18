"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";

const EXEC_TIME_MS = 38;
const DEFAULT_COST_PER_POD_HR = 98.32;
const PASTEL_BLUE = "#7B9DB5";

function computeMetrics(throughput: number, slaSec: number, costPerPodHr: number) {
  const podCapacity = Math.floor((slaSec * 1000) / EXEC_TIME_MS);
  const steadyPods = Math.max(1, Math.ceil(throughput / podCapacity));
  const burstPods = Math.ceil(steadyPods * 1.3);
  const warmReserve = Math.max(1, Math.ceil(steadyPods * 0.25));
  const queueDepth = Math.max(0, throughput - steadyPods * podCapacity);
  const p95latency = EXEC_TIME_MS + (queueDepth > 0 ? (queueDepth / throughput) * 1000 : 0);
  const costPerHour = steadyPods * costPerPodHr;
  const loadPct = Math.min(100, Math.round((throughput / (steadyPods * podCapacity)) * 100));
  return { steadyPods, burstPods, warmReserve, queueDepth, p95latency, costPerHour, loadPct };
}

function MiniChart({ throughput, slaSec }: { throughput: number; slaSec: number }) {
  const points = useMemo(() => {
    const pts = [];
    for (let t = 0; t <= 60; t++) {
      const burst = t > 20 && t < 40;
      const rps = burst ? throughput * 1.8 : throughput;
      const qd = Math.max(0, rps - 40 * Math.floor(slaSec * 1000 / EXEC_TIME_MS));
      const p95 = EXEC_TIME_MS + (qd > 0 ? 50 : 0);
      pts.push({ t, rps, qd, p95 });
    }
    return pts;
  }, [throughput, slaSec]);

  const maxRps = Math.max(...points.map((p) => p.rps), 1);
  const w = 500;
  const h = 80;

  const toX = (t: number) => (t / 60) * w;
  const toY = (v: number, max: number) => h - (v / max) * (h - 4);

  const rpsPath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${toX(p.t)} ${toY(p.rps, maxRps)}`).join(" ");
  const qdPath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${toX(p.t)} ${toY(p.qd, maxRps)}`).join(" ");

  return (
    <div className="border" style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}>
      <p className="font-mono text-[11px] uppercase tracking-[0.12em] px-4 pt-3" style={{ color: "var(--ink-mute)" }}>
        Prometheus: request rate · queue depth · tail latency
      </p>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height: 80 }}>
        <path d={rpsPath} fill="none" stroke={PASTEL_BLUE} strokeWidth={1.5} />
        <path d={qdPath} fill="none" stroke="var(--signal-warm)" strokeWidth={1} strokeDasharray="4 2" />
      </svg>
      <div className="flex gap-4 px-4 pb-3 font-mono text-[11px]">
        <span style={{ color: PASTEL_BLUE }}>── request rate</span>
        <span style={{ color: "var(--signal-warm)" }}>╌ queue depth</span>
      </div>
    </div>
  );
}

export default function AutoscalerSimulator() {
  const [throughput, setThroughput] = useState(400);
  const [slaSec, setSlaSec] = useState(0.2);
  const [costPerPodHr, setCostPerPodHr] = useState(DEFAULT_COST_PER_POD_HR);

  const m = computeMetrics(throughput, slaSec, costPerPodHr);

  return (
    <div className="flex flex-col gap-6">
      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {([
          { label: `Throughput: ${throughput} fps`, min: 10, max: 5000, step: 10, val: throughput, set: setThroughput },
          { label: `SLA target: ${(slaSec * 1000).toFixed(0)} ms`, min: 0.05, max: 1, step: 0.05, val: slaSec, set: setSlaSec },
          { label: `$/h per pod: $${costPerPodHr.toFixed(2)}`, min: 10, max: 400, step: 5, val: costPerPodHr, set: setCostPerPodHr },
        ] as const).map((ctrl) => (
          <div key={ctrl.label} className="flex flex-col gap-1">
            <label className="font-mono text-[12px] uppercase tracking-[0.1em]" style={{ color: "var(--ink-mute)" }}>
              {ctrl.label}
            </label>
            <input
              type="range"
              min={ctrl.min}
              max={ctrl.max}
              step={ctrl.step}
              value={ctrl.val}
              onChange={(e) => (ctrl.set as (v: number) => void)(+e.target.value)}
              className="w-full"
            />
          </div>
        ))}
      </div>

      {/* Chart */}
      <MiniChart throughput={throughput} slaSec={slaSec} />

      {/* GPU pod grid */}
      <div className="flex flex-col gap-3">
        <p className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
          GPU pod grid - {m.steadyPods} steady + {m.warmReserve} warm reserve
        </p>
        <div className="flex flex-wrap gap-2">
          <AnimatePresence>
            {Array.from({ length: m.burstPods }).map((_, i) => {
              const isSteady = i < m.steadyPods;
              const isWarm = i >= m.steadyPods && i < m.steadyPods + m.warmReserve;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ delay: i * 0.03, duration: 0.2 }}
                  className="border flex flex-col items-center justify-center"
                  style={{
                    width: 72,
                    height: 64,
                    borderColor: isSteady ? PASTEL_BLUE : "var(--rule)",
                    backgroundColor: isSteady ? "var(--bg-elev)" : "var(--bg)",
                  }}
                >
                  <p
                    className="font-mono text-[10px] uppercase"
                    style={{ color: isSteady ? PASTEL_BLUE : "var(--ink-mute)" }}
                  >
                    {isSteady ? "H100" : isWarm ? "warm" : "burst"}
                  </p>
                  <p className="font-mono text-[11px]" style={{ color: "var(--ink)" }}>
                    {isSteady ? m.loadPct : isWarm ? "n/a" : "0"}%
                  </p>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      {/* Side summary */}
      <div
        className="border p-5 font-mono text-[13px] flex flex-col gap-2"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)", color: "var(--ink-mute)" }}
      >
        <p>
          At <strong style={{ color: "var(--ink)" }}>{throughput.toLocaleString()} fps</strong> with a{" "}
          <strong style={{ color: "var(--ink)" }}>{(slaSec * 1000).toFixed(0)} ms</strong> tail SLA, the HPA holds{" "}
          <strong style={{ color: PASTEL_BLUE }}>{m.steadyPods} H100 pod{m.steadyPods !== 1 ? "s" : ""}</strong>.
        </p>
        <p>
          Steady-state cost:{" "}
          <strong style={{ color: "var(--ink)" }}>${m.costPerHour.toFixed(2)}/hr</strong>.{" "}
          Burst reserve: <strong style={{ color: "var(--ink)" }}>{m.warmReserve}</strong> pod{m.warmReserve !== 1 ? "s" : ""} warm for 2× spikes.
        </p>
        <p style={{ color: "var(--ink-mute)" }}>
          Based on {EXEC_TIME_MS} ms kernel budget per fingerprint · $/h defaults to AWS p5 on-demand.
        </p>
      </div>
    </div>
  );
}
