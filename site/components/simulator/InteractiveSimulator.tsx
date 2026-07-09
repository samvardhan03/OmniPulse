"use client";

import { useReducer, useCallback } from "react";
import { motion } from "framer-motion";
import Eyebrow from "@/components/primitives/Eyebrow";
import HairlineRule from "@/components/primitives/HairlineRule";
import PythonLane from "./lanes/PythonLane";
import ShmPointerLane from "./lanes/ShmPointerLane";
import JsonRpcLane from "./lanes/JsonRpcLane";
import RustLane from "./lanes/RustLane";
import FfiBridgeLane from "./lanes/FfiBridgeLane";
import KernelLane from "./lanes/KernelLane";
import HnswLane from "./lanes/HnswLane";
import { deriveShmName, buildJsonRpcEnvelope } from "./data/shaHexName";

type SimStep =
  | "idle"
  | "ingested"
  | "shm-pinned"
  | "in-flight"
  | "ffi-bridge"
  | "kernel-running"
  | "completed";

interface SimState {
  step: SimStep;
  shmName: string;
  envelope: object | null;
  useGpu: boolean;
  insertCount: number;
  config: { j: number; q: number; depth: number; jtfs: boolean; dim: number };
}

type SimAction =
  | { type: "UPLOAD"; bytes: Uint8Array; sampleRate: number }
  | { type: "ADVANCE" }
  | { type: "TOGGLE_GPU" }
  | { type: "SET_J"; value: number }
  | { type: "SET_Q"; value: number }
  | { type: "RESET" };

const STEP_ORDER: SimStep[] = [
  "idle",
  "ingested",
  "shm-pinned",
  "in-flight",
  "ffi-bridge",
  "kernel-running",
  "completed",
];

const STEP_LABELS: Record<SimStep, string> = {
  idle: "Upload audio",
  ingested: "Tensor ingested",
  "shm-pinned": "SHM pinned",
  "in-flight": "RPC in-flight",
  "ffi-bridge": "FFI bridge",
  "kernel-running": "Kernel running",
  completed: "Completed",
};

const DEFAULT_CONFIG = { j: 8, q: 16, depth: 2, jtfs: false, dim: 172 };

function reducer(state: SimState, action: SimAction): SimState {
  switch (action.type) {
    case "UPLOAD": {
      const name = deriveShmName(action.bytes);
      const env = buildJsonRpcEnvelope(name, action.bytes.length / 4, action.sampleRate, state.config);
      return { ...state, step: "ingested", shmName: name, envelope: env };
    }
    case "ADVANCE": {
      const idx = STEP_ORDER.indexOf(state.step);
      const next = STEP_ORDER[Math.min(idx + 1, STEP_ORDER.length - 1)];
      const insertCount = next === "completed" ? state.insertCount + 1 : state.insertCount;
      return { ...state, step: next, insertCount };
    }
    case "TOGGLE_GPU":
      return { ...state, useGpu: !state.useGpu };
    case "SET_J":
      return { ...state, config: { ...state.config, j: action.value } };
    case "SET_Q":
      return { ...state, config: { ...state.config, q: action.value } };
    case "RESET":
      return { ...INITIAL, insertCount: state.insertCount };
  }
}

const INITIAL: SimState = {
  step: "idle",
  shmName: "",
  envelope: null,
  useGpu: false,
  insertCount: 0,
  config: DEFAULT_CONFIG,
};

export default function InteractiveSimulator() {
  const [state, dispatch] = useReducer(reducer, INITIAL);

  const handleFile = useCallback(async (file: File) => {
    const ctx = new AudioContext();
    const buf = await file.arrayBuffer();
    const decoded = await ctx.decodeAudioData(buf);
    const offline = new OfflineAudioContext(1, decoded.length, 44100);
    const src = offline.createBufferSource();
    src.buffer = decoded;
    src.connect(offline.destination);
    src.start();
    const rendered = await offline.startRendering();
    const f32 = rendered.getChannelData(0);
    const bytes = new Uint8Array(f32.buffer);
    dispatch({ type: "UPLOAD", bytes, sampleRate: 44100 });
  }, []);

  const stepIdx = STEP_ORDER.indexOf(state.step);
  const isActive = (s: SimStep) => STEP_ORDER.indexOf(s) <= stepIdx;

  const clipboardCmd = `pip install omni-wst-core omnipulse-agent
cargo install omnipulse-mcp
export ANTHROPIC_API_KEY=sk-ant-...
python -m omnipulse_agent.run --wav your.wav`;

  return (
    <section id="simulator" style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>Interactive simulator</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            The fingerprint pipeline, step by step
          </h2>
          <p style={{ color: "var(--ink-mute)", fontSize: 16, maxWidth: 560 }}>
            Drop a WAV file. Step through each swimlane. Every value is
            deterministically computed from your input, no server calls.
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left rail: step indicators */}
          <div className="col-span-12 md:col-span-2 flex md:flex-col gap-2 overflow-x-auto md:overflow-visible">
            {STEP_ORDER.map((s, i) => (
              <div
                key={s}
                className="flex items-center gap-2 shrink-0"
              >
                <div
                  className="w-2 h-2 rounded-full border shrink-0"
                  style={{
                    borderColor: "var(--accent)",
                    backgroundColor: STEP_ORDER.indexOf(state.step) >= i ? "var(--accent)" : "transparent",
                  }}
                />
                <span
                  className="font-mono text-[11px] uppercase tracking-[0.1em] whitespace-nowrap"
                  style={{ color: STEP_ORDER.indexOf(state.step) >= i ? "var(--ink)" : "var(--ink-mute)" }}
                >
                  {STEP_LABELS[s]}
                </span>
              </div>
            ))}
          </div>

          {/* Centre: swimlanes */}
          <div className="col-span-12 md:col-span-7 flex flex-col gap-5">
            {/* Upload zone */}
            {state.step === "idle" && (
              <label
                className="flex flex-col items-center justify-center p-12 border-2 border-dashed cursor-pointer transition-opacity hover:opacity-70"
                style={{ borderColor: "var(--rule)" }}
              >
                <input
                  type="file"
                  accept="audio/*"
                  className="sr-only"
                  onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                />
                <span className="font-mono text-[13px]" style={{ color: "var(--ink-mute)" }}>
                  Drop or click to upload a WAV file
                </span>
                <span className="font-mono text-[11px] mt-1" style={{ color: "var(--ink-mute)" }}>
                  Decoded in-browser via AudioContext · no upload
                </span>
              </label>
            )}

            <PythonLane active={isActive("ingested")} shmName={state.shmName} />
            <ShmPointerLane active={isActive("shm-pinned")} shmName={state.shmName} />
            <JsonRpcLane active={isActive("in-flight")} envelope={state.envelope} />
            <RustLane active={isActive("ffi-bridge")} />
            <FfiBridgeLane active={isActive("kernel-running")} />
            <KernelLane
              active={isActive("kernel-running")}
              useGpu={state.useGpu}
              onToggle={() => dispatch({ type: "TOGGLE_GPU" })}
            />
            <HnswLane active={isActive("completed")} insertCount={state.insertCount} />

            <div className="flex gap-3 flex-wrap mt-2">
              {state.step !== "idle" && state.step !== "completed" && (
                <button
                  onClick={() => dispatch({ type: "ADVANCE" })}
                  className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
                  style={{ borderColor: "var(--accent)", color: "var(--accent)" }}
                >
                  Next step →
                </button>
              )}
              {state.step !== "idle" && (
                <button
                  onClick={() => dispatch({ type: "RESET" })}
                  className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
                  style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
                >
                  Reset
                </button>
              )}
              {state.step === "completed" && (
                <button
                  onClick={() => navigator.clipboard.writeText(clipboardCmd)}
                  className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
                  style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
                >
                  Copy &quot;run locally&quot; CLI
                </button>
              )}
            </div>
          </div>

          {/* Right rail: config */}
          <div className="col-span-12 md:col-span-3 flex flex-col gap-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em]" style={{ color: "var(--ink-mute)" }}>
              WstConfig
            </p>
            {(["j", "q"] as const).map((key) => (
              <div key={key} className="flex flex-col gap-1">
                <label className="font-mono text-[12px] uppercase" style={{ color: "var(--ink-mute)" }}>
                  {key.toUpperCase()} = {state.config[key]}
                </label>
                <input
                  type="range"
                  min={key === "j" ? 4 : 8}
                  max={key === "j" ? 12 : 32}
                  step={key === "j" ? 1 : 4}
                  value={state.config[key]}
                  onChange={(e) =>
                    dispatch({ type: key === "j" ? "SET_J" : "SET_Q", value: +e.target.value })
                  }
                  className="w-full accent-[var(--accent)]"
                />
              </div>
            ))}
            <div className="flex items-center gap-2 mt-2">
              <input
                type="checkbox"
                id="jtfs"
                checked={state.config.jtfs}
                onChange={(e) =>
                  dispatch({ type: "SET_J", value: state.config.j })
                }
                className="accent-[var(--accent)]"
              />
              <label htmlFor="jtfs" className="font-mono text-[12px]" style={{ color: "var(--ink)" }}>
                JTFS
              </label>
            </div>

            <HairlineRule className="mt-2" />

            <div className="flex flex-col gap-1">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
                Kernel
              </p>
              <p
                className="font-mono text-[12px]"
                style={{ color: state.useGpu ? "var(--accent)" : "var(--ink)" }}
              >
                {state.useGpu ? "CUDA Hopper" : "CPU Morlet (Radix-2 FFT)"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
