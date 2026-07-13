"use client";

import { useState } from "react";

interface Attack {
  id: string;
  label: string;
  legacyDrop: number;
  wstDrop: number;
  jtfsDrop: number;
  note?: string;
}

const ATTACKS: Attack[] = [
  {
    id: "pitch",
    label: "pitch shift +10%",
    legacyDrop: 0.72,
    wstDrop: 0.06,
    jtfsDrop: 0.03,
  },
  {
    id: "stretch",
    label: "time stretch",
    legacyDrop: 0.68,
    wstDrop: 0.08,
    jtfsDrop: 0.04,
  },
  {
    id: "mp3",
    label: "MP3 re-encode",
    legacyDrop: 0.55,
    wstDrop: 0.05,
    jtfsDrop: 0.02,
  },
  {
    id: "phase",
    label: "inaudible phase rotation",
    legacyDrop: 0.85,
    wstDrop: 0.80,
    jtfsDrop: 0.07,
    note:
      "This attack defeated standard scattering too. JTFS closes it by measuring the cross-band structure the rotation disturbs.",
  },
];

const BASE_LEGACY = 0.92;
const BASE_WST = 0.88;
const BASE_JTFS = 0.94;

function MeterBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const pct = Math.max(0, Math.min(1, value));
  const failed = pct < 0.5;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px]" style={{ color: "var(--ink-mute)" }}>
          {label}
        </span>
        <span
          className="font-mono text-[11px]"
          style={{ color: failed ? "var(--signal-warm)" : color }}
        >
          {failed ? "fail" : `${Math.round(pct * 100)}%`}
        </span>
      </div>
      <div
        className="h-[6px] rounded-full overflow-hidden"
        style={{ backgroundColor: "var(--rule)" }}
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct * 100}%`,
            backgroundColor: failed ? "var(--signal-warm)" : color,
          }}
        />
      </div>
    </div>
  );
}

export default function TwoLayerAttackToggle() {
  const [active, setActive] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const legacyScore =
    BASE_LEGACY -
    ATTACKS.filter((a) => active.has(a.id)).reduce((s, a) => s + a.legacyDrop, 0);

  const wstScore =
    BASE_WST -
    ATTACKS.filter((a) => active.has(a.id)).reduce((s, a) => s + a.wstDrop, 0);

  const jtfsScore =
    BASE_JTFS -
    ATTACKS.filter((a) => active.has(a.id)).reduce((s, a) => s + a.jtfsDrop, 0);

  const phaseActive = active.has("phase");
  const phaseAttack = ATTACKS.find((a) => a.id === "phase")!;

  return (
    <div className="flex flex-col gap-4">
      <p
        className="font-mono text-[11px] uppercase tracking-[0.14em]"
        style={{ color: "var(--accent-teal)" }}
      >
        Attack survivability
      </p>

      <div className="flex flex-wrap gap-2">
        {ATTACKS.map((a) => (
          <button
            key={a.id}
            onClick={() => toggle(a.id)}
            aria-pressed={active.has(a.id)}
            className="font-mono text-[11px] uppercase tracking-[0.1em] px-3 py-1.5 border transition-all"
            style={{
              borderColor: active.has(a.id) ? "var(--ink)" : "var(--rule)",
              backgroundColor: active.has(a.id) ? "var(--ink)" : "transparent",
              color: active.has(a.id) ? "var(--bg)" : "var(--ink-mute)",
              cursor: "pointer",
            }}
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <MeterBar
          label="waveform matching (legacy)"
          value={legacyScore}
          color="var(--ink-mute)"
        />
        <MeterBar
          label="OmniPulse (JTFS)"
          value={jtfsScore}
          color="var(--accent-teal)"
        />
        {phaseActive && (
          <div
            className="text-[12px] leading-[1.5] p-3 border"
            style={{
              borderColor: "var(--signal-warm)",
              color: "var(--ink-mute)",
              backgroundColor: "rgba(194,70,31,0.05)",
            }}
          >
            <span style={{ color: "var(--signal-warm)" }} className="font-mono text-[11px] uppercase tracking-[0.1em]">
              Note:
            </span>{" "}
            {phaseAttack.note}
          </div>
        )}
      </div>

      <p
        className="font-mono text-[11px]"
        style={{ color: "var(--ink-mute)", borderTop: "1px solid var(--rule)", paddingTop: 8 }}
      >
        Illustrative demo, not a live benchmark.
      </p>
    </div>
  );
}
