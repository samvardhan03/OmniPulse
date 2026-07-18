"use client";

import { useReducer } from "react";
import { motion, AnimatePresence } from "framer-motion";
import traceRaw from "@/lib/tiers/phase-3-trace.json";

const trace = traceRaw as typeof traceRaw;

const PASTEL_VIOLET = "#9B8DB5";

type Step = 0 | 1 | 2 | 3 | 4;

interface State {
  step: Step;
}

type Action = { type: "ADVANCE" } | { type: "RESET" };

function reducer(s: State, a: Action): State {
  if (a.type === "RESET") return { step: 0 };
  const next = Math.min(s.step + 1, 4) as Step;
  return { step: next };
}

const STEP_LABELS = [
  "Idle",
  "LLM parses prompt",
  "RPC: generate_fingerprint",
  "RPC: compare_fingerprints",
  "Done",
];

export default function PromptRouterStepper() {
  const [state, dispatch] = useReducer(reducer, { step: 0 });

  const activeFrameIdx = state.step >= 2 ? state.step - 2 : -1;
  const activeFrame = trace.frames[activeFrameIdx];
  const activeKernelStages = state.step >= 2 ? trace.kernel_stages.slice(0, (state.step - 1) * 3) : [];

  const llmText = state.step >= 1 ? trace.llm_response.text : "";
  const highlightedTool =
    state.step === 2 ? "generate_fingerprint" : state.step === 3 ? "compare_fingerprints" : "";

  return (
    <div className="flex flex-col gap-6">
      {/* Prompt bar */}
      <div
        className="border p-4 font-mono text-[13px]"
        style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)", color: "var(--ink)" }}
      >
        <span style={{ color: "var(--ink-mute)" }}>Operator prompt: </span>
        {trace.prompt}
      </div>

      {/* Step rail */}
      <div className="flex gap-2 flex-wrap">
        {STEP_LABELS.map((label, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full border shrink-0"
              style={{
                borderColor: PASTEL_VIOLET,
                backgroundColor: state.step >= i ? PASTEL_VIOLET : "transparent",
              }}
            />
            <span
              className="font-mono text-[11px] uppercase tracking-[0.1em]"
              style={{ color: state.step >= i ? "var(--ink)" : "var(--ink-mute)" }}
            >
              {label}
            </span>
            {i < STEP_LABELS.length - 1 && (
              <span style={{ color: "var(--rule)" }}>·</span>
            )}
          </div>
        ))}
      </div>

      {/* Three panes */}
      <div className="flex flex-col gap-4">
        {/* Pane 1 — Claude */}
        <div className="flex flex-col gap-2">
          <p
            className="font-mono text-[11px] uppercase tracking-[0.14em]"
            style={{ color: "var(--ink-mute)" }}
          >
            Pane 1: Anthropic Claude
          </p>
          <div
            className="border p-4 font-mono text-[12px] min-h-[100px]"
            style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)", color: "var(--ink)" }}
          >
            <AnimatePresence mode="wait">
              {state.step >= 1 && (
                <motion.div
                  key="llm"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="whitespace-pre-wrap"
                >
                  {llmText.split(/(generate_fingerprint|compare_fingerprints)/).map((part, i) => {
                    const isHighlighted = part === highlightedTool;
                    return (
                      <span
                        key={i}
                        style={{ color: isHighlighted ? PASTEL_VIOLET : "var(--ink)" }}
                      >
                        {part}
                      </span>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Pane 2: JSON-RPC bus */}
        <div className="flex flex-col gap-2">
          <p
            className="font-mono text-[11px] uppercase tracking-[0.14em]"
            style={{ color: "var(--ink-mute)" }}
          >
            Pane 2: JSON-RPC bus
          </p>
          <div
            className="border p-4 font-mono text-[12px] min-h-[120px] overflow-auto relative"
            style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)", color: "var(--ink)" }}
          >
            <AnimatePresence mode="wait">
              {activeFrame ? (
                <motion.div
                  key={activeFrame.id + activeFrame.direction}
                  initial={{ opacity: 0, x: activeFrame.direction === "client_to_server" ? -12 : 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex flex-col gap-2"
                >
                  <div className="flex items-center gap-4 mb-2">
                    <span style={{ color: "var(--ink-mute)" }}>
                      {activeFrame.direction === "client_to_server" ? "Python → Rust" : "Rust → Python"}
                    </span>
                    <span style={{ color: PASTEL_VIOLET }}>
                      {activeFrame.tool}
                    </span>
                    <span style={{ color: "var(--ink-mute)" }}>
                      +{activeFrame.latency_ms}ms
                    </span>
                  </div>
                  <pre className="text-[11px] overflow-auto max-h-[120px]">
                    {JSON.stringify(activeFrame.payload, null, 2)}
                  </pre>
                </motion.div>
              ) : (
                <span style={{ color: "var(--ink-mute)" }}>No frames yet.</span>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Pane 3: Rust + GPU kernel */}
        <div className="flex flex-col gap-2">
          <p
            className="font-mono text-[11px] uppercase tracking-[0.14em]"
            style={{ color: "var(--ink-mute)" }}
          >
            Pane 3: Rust + GPU kernel
          </p>
          <div
            className="border p-4 font-mono text-[12px] min-h-[80px]"
            style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
          >
            <div className="flex flex-col gap-1">
              {trace.kernel_stages.map((stage, i) => (
                <motion.div
                  key={stage}
                  animate={{ opacity: activeKernelStages.includes(stage) ? 1 : 0.25 }}
                  transition={{ duration: 0.2 }}
                  style={{ color: activeKernelStages.includes(stage) ? PASTEL_VIOLET : "var(--ink-mute)" }}
                >
                  {activeKernelStages.includes(stage) ? "▶ " : "  "}{stage}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Controls + wall-clock */}
      <div className="flex items-center gap-4 flex-wrap">
        {state.step < 4 && (
          <button
            onClick={() => dispatch({ type: "ADVANCE" })}
            className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
            style={{ borderColor: PASTEL_VIOLET, color: PASTEL_VIOLET }}
          >
            {state.step === 0 ? "Run pipeline →" : "Next step →"}
          </button>
        )}
        <button
          onClick={() => dispatch({ type: "RESET" })}
          className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
          style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
        >
          Reset
        </button>

        {state.step >= 4 && (
          <p className="font-mono text-[12px]" style={{ color: "var(--ink-mute)" }}>
            LLM {trace.wall_clock.llm_s}s · stdio {trace.wall_clock.stdio_ms}ms · kernel {trace.wall_clock.kernel_ms}ms · index {trace.wall_clock.index_ms}ms
          </p>
        )}
      </div>
    </div>
  );
}
