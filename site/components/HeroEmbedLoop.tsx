"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const BEAT_DURATION = 2000;
const TOTAL_BEATS = 4;

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return reduced;
}

function DctGrid({ pulse }: { pulse: boolean }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(8, 1fr)",
        gap: 1,
        position: "absolute",
        inset: 0,
      }}
    >
      {Array.from({ length: 64 }, (_, i) => {
        const u = Math.floor(i / 8);
        const v = i % 8;
        const s = u + v;
        const isMid = s >= 2 && s <= 6;
        return (
          <motion.div
            key={i}
            style={{
              border: "0.5px solid rgba(27,27,31,0.15)",
              backgroundColor: isMid
                ? pulse
                  ? "var(--signal-warm)"
                  : "rgba(194,70,31,0.22)"
                : "transparent",
            }}
            animate={
              isMid && pulse
                ? { opacity: [0.4, 1, 0.55, 1, 0.4] }
                : { opacity: 1 }
            }
            transition={
              isMid && pulse
                ? { duration: 1.0, ease: "easeInOut", delay: (u * 8 + v) * 0.008 }
                : { duration: 0 }
            }
          />
        );
      })}
    </div>
  );
}

const BITS = "10110010 11001011 01101100 10110010";

function BitsSlide() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      style={{
        position: "absolute",
        bottom: 20,
        left: 12,
        right: 12,
        backgroundColor: "rgba(27,27,31,0.82)",
        padding: "8px 10px",
        borderRadius: 2,
      }}
    >
      <p
        className="font-mono"
        style={{ fontSize: 11, color: "var(--signal-warm)", letterSpacing: "0.08em" }}
      >
        {BITS}
      </p>
      <p className="font-mono" style={{ fontSize: 9, color: "rgba(255,255,255,0.5)", marginTop: 3 }}>
        signed ID
      </p>
    </motion.div>
  );
}

function Shimmer() {
  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 0.18, 0, 0.12, 0] }}
        transition={{ duration: 1.6, times: [0, 0.2, 0.45, 0.7, 1] }}
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: "var(--bg-elev)",
          mixBlendMode: "overlay",
          pointerEvents: "none",
        }}
      />
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.6 }}
        style={{
          position: "absolute",
          bottom: 12,
          left: 10,
          right: 10,
          backgroundColor: "rgba(27,27,31,0.75)",
          padding: "6px 8px",
          borderRadius: 2,
        }}
      >
        <p className="font-mono" style={{ fontSize: 9, color: "rgba(255,255,255,0.55)" }}>
          re-encoded, cropped, re-uploaded
        </p>
      </motion.div>
    </>
  );
}

function VerdictChip() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      style={{
        position: "absolute",
        bottom: 20,
        left: "50%",
        transform: "translateX(-50%)",
        backgroundColor: "rgba(42,157,143,0.12)",
        border: "1px solid var(--accent-teal)",
        padding: "6px 14px",
        borderRadius: 2,
        whiteSpace: "nowrap",
      }}
    >
      <span
        className="font-mono"
        style={{ fontSize: 11, color: "var(--accent-teal)", letterSpacing: "0.1em" }}
      >
        Verified: Exact
      </span>
    </motion.div>
  );
}

export default function HeroEmbedLoop() {
  const reduced = usePrefersReducedMotion();
  const [beat, setBeat] = useState(reduced ? 3 : 0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (reduced) return;
    timerRef.current = setTimeout(function tick() {
      setBeat((b) => (b + 1) % TOTAL_BEATS);
      timerRef.current = setTimeout(tick, BEAT_DURATION);
    }, BEAT_DURATION);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [reduced]);

  return (
    <div className="flex flex-col gap-3">
      {/* Video frame */}
      <div
        style={{
          position: "relative",
          width: "100%",
          aspectRatio: "16/10",
          backgroundColor: "var(--bg-elev)",
          border: "1px solid var(--rule)",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        {/* Subtle gradient placeholder image */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(135deg, rgba(194,70,31,0.06) 0%, rgba(42,157,143,0.06) 100%)",
          }}
        />

        {/* Beat 0: DCT grid fades in with mid-band pulse */}
        <AnimatePresence>
          {(beat === 0 || reduced === false) && (beat === 0 || beat === 3) ? (
            <motion.div
              key="dct"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              style={{ position: "absolute", inset: 0 }}
            >
              <DctGrid pulse={beat === 0} />
            </motion.div>
          ) : null}
        </AnimatePresence>

        {/* Beat 1: bits slide */}
        <AnimatePresence>
          {beat === 1 && <BitsSlide key="bits" />}
        </AnimatePresence>

        {/* Beat 2: shimmer */}
        <AnimatePresence>
          {beat === 2 && (
            <motion.div key="shimmer" style={{ position: "absolute", inset: 0 }}>
              <Shimmer />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Beat 3: verdict chip */}
        <AnimatePresence>
          {beat === 3 && <VerdictChip key="verdict" />}
        </AnimatePresence>

        {/* Beat counter dots */}
        <div
          style={{
            position: "absolute",
            top: 10,
            right: 10,
            display: "flex",
            gap: 4,
          }}
        >
          {Array.from({ length: 4 }, (_, i) => (
            <div
              key={i}
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                backgroundColor:
                  i === beat
                    ? "var(--signal-warm)"
                    : "rgba(27,27,31,0.2)",
                transition: "background-color 0.3s",
              }}
            />
          ))}
        </div>
      </div>

      <p
        className="font-mono text-[11px] text-center"
        style={{ color: "var(--ink-mute)" }}
      >
        The identifier survives what the internet does to media.
      </p>
    </div>
  );
}
