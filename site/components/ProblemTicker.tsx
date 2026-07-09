"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const LINES: { prefix: string; key: string; suffix: string }[] = [
  { prefix: "", key: "A pitch-shifted copy", suffix: " walks straight past waveform matching." },
  { prefix: "", key: "A screenshot", suffix: " strips a C2PA manifest in one keypress." },
  { prefix: "", key: "A provider watermark works perfectly.", suffix: " The provider owns the record." },
];

const INTERVAL_MS = 4000;

export default function ProblemTicker() {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    if (reduced || paused) return;
    timerRef.current = setTimeout(function tick() {
      setIndex((i) => (i + 1) % LINES.length);
      timerRef.current = setTimeout(tick, INTERVAL_MS);
    }, INTERVAL_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [reduced, paused]);

  const line = LINES[reduced ? 0 : index];

  return (
    <div
      className="max-w-[1280px] mx-auto px-6 py-5"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      style={{ borderBottom: "1px solid var(--rule)" }}
    >
      <div className="flex items-center gap-4 min-h-[28px]">
        <span
          className="font-mono text-[11px] uppercase tracking-[0.16em] shrink-0"
          style={{ color: "var(--ink-mute)" }}
        >
          Problem
        </span>
        <div className="w-px h-4 shrink-0" style={{ backgroundColor: "var(--rule)" }} />
        <div className="relative overflow-hidden flex-1">
          <AnimatePresence mode="wait">
            <motion.p
              key={index}
              className="font-mono text-[13px] leading-[1.5]"
              style={{ color: "var(--ink-mute)" }}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <span style={{ color: "var(--signal-warm)" }}>{line.key}</span>
              {line.suffix}
            </motion.p>
          </AnimatePresence>
        </div>
        {!reduced && (
          <div className="flex gap-1.5 shrink-0">
            {LINES.map((_, i) => (
              <div
                key={i}
                style={{
                  width: 4,
                  height: 4,
                  borderRadius: "50%",
                  backgroundColor: i === index ? "var(--signal-warm)" : "rgba(27,27,31,0.18)",
                  transition: "background-color 0.3s",
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
