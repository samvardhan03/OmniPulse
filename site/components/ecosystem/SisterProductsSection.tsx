"use client";

import { useState } from "react";
import Eyebrow from "@/components/primitives/Eyebrow";

const PRODUCTS = [
  {
    wordmark: "ψ Vikshep",
    domain: "SCIENTIFIC COMPUTE · vikshep.vercel.app",
    tagline: "Deterministic features for physics. Nothing learned, nothing leaked.",
    body: "Wavelet scattering features for physics analyses — mass-decorrelated jet tagging, template-free BSM anomaly detection, rotation-invariant field inference. Because the filters are fixed by the mathematics of the scattering transform and not by training, the features cannot secretly encode the resonance mass — so a downstream cut cannot sculpt a fake bump into a smooth background. Currently in pilot with the University of Edinburgh on Geant4-simulated ATLAS diboson data.",
    stats: [
      "1-D / 2-D / 3-D runtime config",
      "SE(2) · SO(3) invariance",
      "r₂ + DisCo decorrelation",
    ],
    cta: "Visit Vikshep →",
    href: "https://vikshep.vercel.app",
  },
  {
    wordmark: "📡 Drift",
    domain: "SYSTEMATIC ALPHA · drift-site-livid.vercel.app",
    tagline: "From log-returns to alpha. Seven layers. Zero black boxes.",
    body: "Quantitative research platform built on the same scattering core. Cauchy wavelet features over log-returns, rank-transform IC/ICIR signal composition, Black-Litterman and HRP portfolio construction. Every formula is implemented directly from first principles — no hidden models, every step derivable from the build history. 182 tests, 0.70 Sharpe on the 3-year synthetic HRP backtest, MCP-native.",
    stats: [
      "7 layers from data to weights",
      "182 tests passing",
      "Sharpe 0.70 · PSR 0.886",
    ],
    cta: "Visit Drift →",
    href: "https://drift-site-livid.vercel.app",
  },
] as const;

function ProductCard({ product }: { product: (typeof PRODUCTS)[number] }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="flex flex-col gap-4 p-8 transition-colors cursor-pointer"
      style={{
        backgroundColor: hovered ? "var(--bg-elev)" : "var(--bg)",
        borderRight: "1px solid var(--rule)",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="flex flex-col gap-1">
        <p
          className="font-mono text-[11px] uppercase tracking-[0.14em]"
          style={{ color: "var(--ink-mute)" }}
        >
          {product.domain}
        </p>
        <h3
          className="font-serif font-light text-[22px] leading-tight"
          style={{ color: "var(--ink)" }}
        >
          {product.wordmark}
        </h3>
        <p
          className="font-mono text-[12px] leading-snug"
          style={{ color: "var(--ink-mute)" }}
        >
          {product.tagline}
        </p>
      </div>

      <p className="text-[15px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
        {product.body}
      </p>

      <p
        className="font-mono text-[11px] leading-[1.9] mt-auto pt-3"
        style={{ borderTop: "1px solid var(--rule)", color: "var(--ink-mute)" }}
      >
        {product.stats.map((s) => (
          <span key={s} className="block">
            · {s}
          </span>
        ))}
      </p>

      <a
        href={product.href}
        target="_blank"
        rel="noopener noreferrer"
        className="font-mono text-[13px] uppercase tracking-[0.12em] transition-opacity hover:opacity-70 self-start"
        style={{ color: "var(--ink)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {product.cta}
      </a>
    </div>
  );
}

export default function SisterProductsSection() {
  return (
    <section id="ecosystem" style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>Built on the same engine</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            Two sister products. Same data plane. Different physics.
          </h2>
          <p
            className="text-[17px] leading-[1.6] max-w-[640px]"
            style={{ color: "var(--ink-mute)" }}
          >
            The OmniPulse scattering engine — omni-wst-core, omni-ffi, sliced-wasserstein,
            vector-index — also runs at the heart of two independent product surfaces. Same
            zero-copy core, same mathematical guarantees, completely different markets.
          </p>
        </div>

        <div
          className="grid grid-cols-1 md:grid-cols-2 gap-px"
          style={{ border: "1px solid var(--rule)" }}
        >
          {PRODUCTS.map((p) => (
            <ProductCard key={p.wordmark} product={p} />
          ))}
        </div>

        <p
          className="mt-8 text-center font-mono text-[12px]"
          style={{ color: "var(--ink-mute)" }}
        >
          Three product surfaces. One engine, dual-licensed AGPL-3.0 + Commercial.
          Maintained by the same two people.
        </p>
      </div>
    </section>
  );
}
