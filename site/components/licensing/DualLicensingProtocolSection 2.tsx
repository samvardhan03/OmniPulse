import Eyebrow from "@/components/primitives/Eyebrow";
import HairlineRule from "@/components/primitives/HairlineRule";

const rows = [
  { label: "Source code access", oss: "✓ full", commercial: "✓ full" },
  { label: "Modify and redistribute", oss: "✓", commercial: "✓ (subject to contract)" },
  { label: "Production deployment", oss: "⚠ research", commercial: "✓" },
  { label: "Closed-source distribution", oss: "✗", commercial: "✓" },
  { label: "SLA / support", oss: "✗", commercial: "✓ 24/7 enterprise" },
  { label: "GPU autoscaling deployment", oss: "✗", commercial: "✓" },
  { label: "License-token issuance volume", oss: "unlimited test", commercial: "contracted tier" },
  { label: "Ed25519 key custody", oss: "self-managed", commercial: "managed HSM optional" },
  { label: "IPFS pinning service", oss: "self-hosted", commercial: "managed" },
  { label: "Audit attestations", oss: "community", commercial: "SOC 2 + ISO 27001 (roadmap)" },
  { label: "Indemnification", oss: "✗", commercial: "✓" },
];

export default function DualLicensingProtocolSection() {
  return (
    <section id="licensing" style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>Dual licensing protocol</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            Apache 2.0 vs Commercial Enterprise
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--rule)" }}>
                <th className="text-left py-3 pr-8 font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)", width: "40%" }}>
                  Capability
                </th>
                <th className="text-left py-3 px-4 font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: "var(--ink)" }}>
                  Apache 2.0
                </th>
                <th className="text-left py-3 pl-8 font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: "var(--accent)" }}>
                  Commercial Enterprise
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--rule)" }}>
                  <td className="py-4 pr-8 text-[15px]" style={{ color: "var(--ink-mute)" }}>
                    {row.label}
                  </td>
                  <td
                    className="py-4 px-4 font-mono text-[13px]"
                    style={{
                      color:
                        row.oss.startsWith("✓")
                          ? "var(--ink)"
                          : row.oss.startsWith("✗")
                          ? "var(--ink-mute)"
                          : "var(--signal-warm)",
                    }}
                  >
                    {row.oss}
                  </td>
                  <td
                    className="py-4 pl-8 font-mono text-[13px]"
                    style={{ color: "var(--ink)" }}
                  >
                    {row.commercial}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-10 flex flex-col gap-2 max-w-[640px]">
          <p className="text-[15px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
            Every Rust crate and Python module in this workspace is published
            under the <code className="font-mono text-[13px]">Apache-2.0</code>{" "}
            SPDX identifier (see{" "}
            <code className="font-mono text-[12px]">omnipulse-rs/Cargo.toml:16</code>). Commercial
            enterprise agreements unlock production SLAs, managed infrastructure,
            and indemnification.
          </p>
          <p className="text-[15px]" style={{ color: "var(--ink-mute)" }}>
            Commercial inquiries:{" "}
            <a
              href="mailto:shekhawatsamvardhan@gmail.com"
              className="transition-opacity hover:opacity-60"
              style={{ color: "var(--ink)" }}
            >
              shekhawatsamvardhan@gmail.com
            </a>
          </p>
        </div>
      </div>
    </section>
  );
}
