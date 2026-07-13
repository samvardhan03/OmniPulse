"use client";

import { useState } from "react";

type Band = "low" | "mid" | "high";

function getBand(u: number, v: number): Band {
  const s = u + v;
  if (s < 2) return "low";
  if (s <= 6) return "mid";
  return "high";
}

const BAND_LABELS: Record<Band, string> = {
  low: "Visible to the eye: embedding here would be seen.",
  mid: "The survivable corridor: codecs keep it, eyes ignore it. The identifier lives here.",
  high: "First thing compression deletes: embedding here would not survive.",
};

const BAND_EYEBROWS: Record<Band, string> = {
  low: "Low band (u+v < 2)",
  mid: "Mid band (2 <= u+v <= 6)",
  high: "High band (u+v > 6)",
};

export default function TwoLayerDctExplorer() {
  const [hovered, setHovered] = useState<{ u: number; v: number } | null>(null);

  const band = hovered ? getBand(hovered.u, hovered.v) : null;

  return (
    <div className="flex flex-col gap-3">
      <p
        className="font-mono text-[11px] uppercase tracking-[0.14em]"
        style={{ color: "var(--signal-warm)" }}
      >
        DCT band explorer
      </p>
      <div
        className="inline-grid"
        style={{ gridTemplateColumns: "repeat(8, 28px)", gap: 2 }}
        role="grid"
        aria-label="8x8 DCT coefficient grid"
      >
        {Array.from({ length: 8 }, (_, u) =>
          Array.from({ length: 8 }, (_, v) => {
            const b = getBand(u, v);
            const isHov = hovered?.u === u && hovered?.v === v;
            return (
              <button
                key={`${u}-${v}`}
                role="gridcell"
                aria-label={`DCT cell u=${u} v=${v}: ${BAND_EYEBROWS[b]}`}
                onMouseEnter={() => setHovered({ u, v })}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered({ u, v })}
                onBlur={() => setHovered(null)}
                style={{
                  width: 28,
                  height: 28,
                  border: "1px solid",
                  borderColor: isHov ? "var(--ink)" : "var(--rule)",
                  backgroundColor:
                    b === "mid"
                      ? isHov
                        ? "var(--signal-warm)"
                        : "rgba(194, 70, 31, 0.18)"
                      : b === "low"
                      ? isHov
                        ? "var(--ink-mute)"
                        : "rgba(27,27,31,0.08)"
                      : "transparent",
                  cursor: "default",
                  transition: "background-color 0.1s",
                }}
              />
            );
          })
        )}
      </div>

      <div style={{ minHeight: 48 }}>
        {band ? (
          <div className="flex flex-col gap-1">
            <p
              className="font-mono text-[10px] uppercase tracking-[0.14em]"
              style={{
                color:
                  band === "mid"
                    ? "var(--signal-warm)"
                    : "var(--ink-mute)",
              }}
            >
              {BAND_EYEBROWS[band]}
            </p>
            <p className="text-[13px] leading-[1.5]" style={{ color: "var(--ink-mute)" }}>
              {BAND_LABELS[band]}
            </p>
          </div>
        ) : (
          <p className="text-[13px]" style={{ color: "var(--ink-mute)" }}>
            Hover or tab to any cell to see its role.
          </p>
        )}
      </div>

      <p
        className="font-mono text-[11px] leading-[1.6]"
        style={{ color: "var(--ink-mute)", borderTop: "1px solid var(--rule)", paddingTop: 8 }}
      >
        25 of 64 coefficients per block: chosen by codec physics, not by preference.
      </p>
    </div>
  );
}
