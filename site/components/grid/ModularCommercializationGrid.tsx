"use client";

import Link from "next/link";
import Eyebrow from "@/components/primitives/Eyebrow";

export const TIERS = [
  {
    phase: "I",
    title: "Phase I — Institutional Research",
    sub: "Standalone DSP wheels for desktop labs and HPC clusters. C++/CUDA Wavelet Scattering primitives, no orchestration required. AGPL-3.0 + Commercial.",
    pkg: "pip install omni-wst-core",
    externalHref: "https://pypi.org/project/omni-wst-core/",
    externalLabel: "↗ View on PyPI",
    deepdiveHref: "/tiers/phase-1-dsp",
    commercial: false,
  },
  {
    phase: "II",
    title: "Phase II — High-Velocity Concurrent Processing",
    sub: "The vector substrate. omni-hnsw + sliced-wasserstein Rust crates for sub-millisecond nearest-neighbour over billion-scale fingerprint catalogues. AGPL-3.0 + Commercial.",
    pkg: "cargo add vector-index sliced-wasserstein",
    externalHref: "https://crates.io/crates/vector-index",
    externalLabel: "↗ View on crates.io",
    deepdiveHref: "/tiers/phase-2-vector",
    commercial: false,
  },
  {
    phase: "III",
    title: "Phase III — Autonomous Agentic Control",
    sub: "Drop-in MCP server. omnipulse-agent parses operator requests and routes them to the Rust orchestrator over line-delimited JSON-RPC 2.0. AGPL-3.0 + Commercial.",
    pkg: "pip install omnipulse-agent",
    externalHref: "https://pypi.org/project/omnipulse-agent/",
    externalLabel: "↗ View on PyPI",
    deepdiveHref: "/tiers/phase-3-agent",
    commercial: false,
  },
  {
    phase: "ENTERPRISE",
    title: "Enterprise SaaS Pipeline",
    sub: "Cloud-native multi-tenant deployment. Kubernetes control plane, GPU autoscaling driven by Prometheus queue depth, ed25519-signed license tokens, IPFS pinning.",
    pkg: "",
    externalHref: "mailto:shekhawatsamvardhan@gmail.com",
    externalLabel: "Talk to founders →",
    deepdiveHref: "/tiers/enterprise",
    commercial: true,
  },
] as const;

function DspGraphic() {
  return (
    <svg viewBox="0 0 88 44" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 88, height: 44 }}>
      <path
        d="M0,22 C8,22 8,5 18,5 C28,5 28,39 38,39 C48,39 48,12 58,12 C68,12 68,28 78,28 C83,28 86,22 88,22"
        stroke="#7B9DB5"
        strokeWidth="1.5"
        opacity="0.7"
      />
      <path
        d="M0,22 C8,22 8,10 18,10 C28,10 28,34 38,34 C48,34 48,16 58,16 C68,16 68,26 78,26 C83,26 86,22 88,22"
        stroke="#7B9DB5"
        strokeWidth="0.8"
        opacity="0.35"
      />
    </svg>
  );
}

function HnswGraphic() {
  const nodes = [
    { cx: 12, cy: 22 },
    { cx: 38, cy: 8 },
    { cx: 38, cy: 36 },
    { cx: 64, cy: 15 },
    { cx: 64, cy: 29 },
    { cx: 82, cy: 22 },
  ];
  const edges = [[0,1],[0,2],[1,3],[2,4],[3,5],[4,5],[1,4],[2,3]];
  return (
    <svg viewBox="0 0 94 44" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 94, height: 44 }}>
      {edges.map(([s, t], i) => (
        <line
          key={i}
          x1={nodes[s].cx} y1={nodes[s].cy}
          x2={nodes[t].cx} y2={nodes[t].cy}
          stroke="#8FB5A4"
          strokeWidth="0.9"
          opacity="0.5"
        />
      ))}
      {nodes.map((n, i) => (
        <circle key={i} cx={n.cx} cy={n.cy} r={i === 0 || i === 5 ? 5 : 3.5} fill="#8FB5A4" opacity="0.75" />
      ))}
    </svg>
  );
}

function AgentGraphic() {
  return (
    <svg viewBox="0 0 88 44" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 88, height: 44 }}>
      <circle cx="14" cy="22" r="6" fill="#9B8DB5" opacity="0.75" />
      <line x1="20" y1="22" x2="40" y2="22" stroke="#9B8DB5" strokeWidth="1.2" opacity="0.6" />
      <circle cx="46" cy="22" r="5" fill="#9B8DB5" opacity="0.6" />
      <line x1="51" y1="18" x2="70" y2="8" stroke="#9B8DB5" strokeWidth="1" opacity="0.55" />
      <line x1="51" y1="26" x2="70" y2="36" stroke="#9B8DB5" strokeWidth="1" opacity="0.55" />
      <circle cx="76" cy="8" r="4" fill="#9B8DB5" opacity="0.65" />
      <circle cx="76" cy="36" r="4" fill="#9B8DB5" opacity="0.65" />
    </svg>
  );
}

function EnterpriseGraphic() {
  const cols = 4;
  const rows = 2;
  return (
    <svg viewBox="0 0 88 44" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 88, height: 44 }}>
      {Array.from({ length: cols * rows }).map((_, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        return (
          <rect
            key={i}
            x={col * 22 + 1}
            y={row * 20 + 2}
            width="17"
            height="14"
            rx="1"
            fill="none"
            stroke="#C2A882"
            strokeWidth="1"
            opacity={i < 4 ? 0.75 : 0.4}
          />
        );
      })}
      {Array.from({ length: cols }).map((_, i) => (
        <circle key={i} cx={i * 22 + 9.5} cy="9" r="2" fill="#C2A882" opacity="0.6" />
      ))}
    </svg>
  );
}

const GRAPHICS: Record<string, React.ReactNode> = {
  I: <DspGraphic />,
  II: <HnswGraphic />,
  III: <AgentGraphic />,
  ENTERPRISE: <EnterpriseGraphic />,
};

export default function ModularCommercializationGrid() {
  return (
    <section id="platform" style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>Modular commercialisation</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            Four tiers, one fingerprint plane
          </h2>
        </div>

        <div
          className="grid grid-cols-1 md:grid-cols-2 gap-px"
          style={{ border: "1px solid var(--rule)" }}
        >
          {TIERS.map((tier) => (
            <Link
              key={tier.phase}
              href={tier.deepdiveHref}
              className="group relative block p-8 transition-colors"
              style={{
                backgroundColor: "var(--bg)",
                borderBottom: "1px solid var(--rule)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-elev)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg)";
              }}
            >
              {/* Pastel graphic — fades in on hover */}
              <div
                className="absolute top-6 right-6 pointer-events-none transition-opacity duration-300"
                style={{ opacity: 0 }}
                ref={(el) => {
                  if (!el) return;
                  const parent = el.closest("a");
                  if (!parent) return;
                  const show = () => { el.style.opacity = "1"; };
                  const hide = () => { el.style.opacity = "0"; };
                  parent.addEventListener("mouseenter", show);
                  parent.addEventListener("mouseleave", hide);
                }}
              >
                {GRAPHICS[tier.phase]}
              </div>

              <div className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex flex-col gap-1">
                    <p
                      className="font-mono text-[11px] uppercase tracking-[0.14em]"
                      style={{ color: "var(--ink-mute)" }}
                    >
                      Phase {tier.phase}
                    </p>
                    <h3
                      className="font-serif font-light text-[22px] leading-tight"
                      style={{ color: "var(--ink)" }}
                    >
                      {tier.title}
                    </h3>
                  </div>
                  {tier.commercial && (
                    <span
                      className="font-mono text-[10px] uppercase tracking-[0.1em] px-2 py-1 border shrink-0"
                      style={{
                        borderColor: "var(--signal-warm)",
                        color: "var(--signal-warm)",
                      }}
                    >
                      Commercial
                    </span>
                  )}
                </div>

                <p className="text-[15px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
                  {tier.sub}
                </p>

                {tier.pkg ? (
                  <code
                    className="font-mono text-[12px] px-3 py-2 border block"
                    style={{
                      borderColor: "var(--rule)",
                      backgroundColor: "var(--bg)",
                      color: "var(--ink)",
                    }}
                  >
                    {tier.pkg}
                  </code>
                ) : null}

                {/* Primary CTA — "Know how it works" */}
                <div className="flex flex-col gap-2 mt-2">
                  <span
                    className="font-mono text-[13px] uppercase tracking-[0.12em] transition-opacity"
                    style={{ color: "var(--ink)" }}
                  >
                    → Know how it works
                  </span>

                  {/* Secondary — external link */}
                  <span
                    className="font-mono text-[11px] uppercase tracking-[0.1em] transition-opacity hover:opacity-60"
                    style={{ color: "var(--ink-mute)" }}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      window.open(tier.externalHref, tier.externalHref.startsWith("mailto") ? "_self" : "_blank");
                    }}
                  >
                    {tier.externalLabel}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
