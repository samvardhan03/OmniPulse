"use client";

import { useEffect, useRef, useState } from "react";
import { buildMorletBank, morletTimeDomain, morletFreqAmplitude, MorletFilter } from "@/lib/morlet";

const PASTEL_BLUE = "#7B9DB5";

export default function FilterBankExplorer() {
  const [j, setJ] = useState(8);
  const [q, setQ] = useState(16);
  const [depth, setDepth] = useState<1 | 2 | 3>(2);
  const [jtfs, setJtfs] = useState(false);
  const [selectedLambda, setSelectedLambda] = useState(0);
  const [tooltip, setTooltip] = useState<string | null>(null);

  const timeDomainRef = useRef<HTMLCanvasElement>(null);
  const bank = buildMorletBank(j, q, depth, jtfs);
  const selected = bank.filters[selectedLambda] ?? bank.filters[0];

  useEffect(() => {
    const canvas = timeDomainRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d")!;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    const signal = morletTimeDomain(selected, 256);
    const max = Math.max(...Array.from(signal).map(Math.abs), 0.01);

    ctx.strokeStyle = PASTEL_BLUE;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    signal.forEach((v, i) => {
      const x = (i / signal.length) * w;
      const y = h / 2 - (v / max) * (h / 2 - 8);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.strokeStyle = "var(--rule)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
  }, [selected]);

  const freqData = morletFreqAmplitude(selected, 256);
  const maxFreq = Math.max(...Array.from(freqData), 0.01);
  const svgH = 120;
  const svgW = 400;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left rail — controls */}
        <div className="flex flex-col gap-5 md:col-span-1">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em]" style={{ color: "var(--ink-mute)" }}>
            WSTConfig
          </p>
          {([["J", j, setJ, 1, 10], ["Q", q, setQ, 1, 32]] as const).map(([label, val, setter, min, max]) => (
            <div key={String(label)} className="flex flex-col gap-1">
              <label className="font-mono text-[12px] uppercase" style={{ color: "var(--ink-mute)" }}>
                {label} = {val}
              </label>
              <input
                type="range"
                min={min}
                max={max}
                step={1}
                value={val}
                onChange={(e) => {
                  (setter as (v: number) => void)(+e.target.value);
                  setSelectedLambda(0);
                }}
                className="w-full"
              />
            </div>
          ))}

          <div className="flex flex-col gap-1">
            <p className="font-mono text-[12px] uppercase" style={{ color: "var(--ink-mute)" }}>
              Depth
            </p>
            <div className="flex gap-2">
              {([1, 2, 3] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setDepth(d)}
                  className="font-mono text-[12px] px-3 py-1 border transition-opacity hover:opacity-70"
                  style={{
                    borderColor: depth === d ? PASTEL_BLUE : "var(--rule)",
                    color: depth === d ? PASTEL_BLUE : "var(--ink-mute)",
                  }}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="jtfs-fb"
              checked={jtfs}
              onChange={(e) => setJtfs(e.target.checked)}
            />
            <label htmlFor="jtfs-fb" className="font-mono text-[12px]" style={{ color: "var(--ink)" }}>
              JTFS
            </label>
          </div>

          <div
            className="p-3 border font-mono text-[12px]"
            style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
          >
            <span style={{ color: PASTEL_BLUE }}>{bank.pathCount.toLocaleString()}</span> scattering paths
            <br />at depth {depth}
          </div>
        </div>

        {/* Main panel */}
        <div className="md:col-span-3 flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Time domain */}
            <div className="flex flex-col gap-2">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
                Time domain: λ={selectedLambda}
              </p>
              <canvas
                ref={timeDomainRef}
                className="w-full border"
                style={{ height: 120, borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
              />
            </div>

            {/* Frequency domain */}
            <div className="flex flex-col gap-2">
              <p className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
                Frequency domain: bank
              </p>
              <div
                className="border relative overflow-hidden"
                style={{ height: 120, borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}
              >
                <svg
                  viewBox={`0 0 ${svgW} ${svgH}`}
                  preserveAspectRatio="none"
                  className="absolute inset-0 w-full h-full"
                >
                  {bank.filters.map((f) => {
                    const freqBin = Array.from(morletFreqAmplitude(f, svgW));
                    const pts = freqBin
                      .map((v, i) => `${i},${svgH - (v / maxFreq) * (svgH - 4)}`)
                      .join(" ");
                    const isSelected = f.lambda === selectedLambda;
                    return (
                      <polyline
                        key={f.lambda}
                        points={pts}
                        fill="none"
                        stroke={isSelected ? PASTEL_BLUE : "var(--rule)"}
                        strokeWidth={isSelected ? 1.5 : 0.6}
                        opacity={isSelected ? 1 : 0.5}
                        style={{ cursor: "pointer" }}
                        onClick={() => setSelectedLambda(f.lambda)}
                        onMouseEnter={() =>
                          setTooltip(
                            `λ=${f.lambda} · ξ=π·2^(-${f.lambda}/${q}) · σ=${f.sigma.toFixed(2)} · peak=${f.peak.toFixed(3)}`
                          )
                        }
                        onMouseLeave={() => setTooltip(null)}
                      />
                    );
                  })}
                </svg>
              </div>
            </div>
          </div>

          {/* Tooltip */}
          <div
            className="font-mono text-[12px] p-3 border min-h-[44px]"
            style={{ borderColor: "var(--rule)", color: "var(--ink-mute)", backgroundColor: "var(--bg-elev)" }}
          >
            {tooltip ?? `Filter λ=${selectedLambda} · ξ=π·2^(-${selectedLambda}/${q}) · σ=${selected.sigma.toFixed(3)} samples · peak=${selected.peak.toFixed(3)} (analytic Morlet, normalised)`}
          </div>

          {/* Filter selector strip */}
          <div className="flex flex-wrap gap-1 max-h-[72px] overflow-y-auto">
            {bank.filters.slice(0, Math.min(j * q, 48)).map((f) => (
              <button
                key={f.lambda}
                onClick={() => setSelectedLambda(f.lambda)}
                className="font-mono text-[10px] px-2 py-0.5 border transition-opacity hover:opacity-70"
                style={{
                  borderColor: f.lambda === selectedLambda ? PASTEL_BLUE : "var(--rule)",
                  color: f.lambda === selectedLambda ? PASTEL_BLUE : "var(--ink-mute)",
                }}
              >
                λ={f.lambda}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
