import Eyebrow from "@/components/primitives/Eyebrow";

const ROWS = [
  {
    aspect: "Who owns the record",
    synthid: "The provider",
    omnipulse: "The creator, on a decentralized ledger",
  },
  {
    aspect: "What it verifies",
    synthid: "Whether content was AI-generated",
    omnipulse: "Whether content is yours, and under what license",
  },
  {
    aspect: "How verification works",
    synthid: "Through the provider's service",
    omnipulse: "Deterministic mathematics anyone can run",
  },
];

export default function TwoLayerSynthIdGrid() {
  return (
    <section style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>Honest comparison</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            SynthID and OmniPulse answer different questions.
          </h2>
          <p className="text-[17px] leading-[1.6] max-w-[640px]" style={{ color: "var(--ink-mute)" }}>
            SynthID answers a different question. Both matter.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--rule)" }}>
                <th
                  className="text-left py-3 pr-8 font-mono text-[12px] uppercase tracking-[0.14em]"
                  style={{ color: "var(--ink-mute)", width: "30%" }}
                >
                  Dimension
                </th>
                <th
                  className="text-left py-3 px-4 font-mono text-[12px] uppercase tracking-[0.14em]"
                  style={{ color: "var(--ink-mute)" }}
                >
                  SynthID (Google DeepMind)
                </th>
                <th
                  className="text-left py-3 pl-8 font-mono text-[12px] uppercase tracking-[0.14em]"
                  style={{ color: "var(--signal-warm)" }}
                >
                  OmniPulse
                </th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--rule)" }}>
                  <td
                    className="py-5 pr-8 text-[15px] font-serif font-light"
                    style={{ color: "var(--ink)" }}
                  >
                    {row.aspect}
                  </td>
                  <td
                    className="py-5 px-4 text-[15px] leading-[1.6]"
                    style={{ color: "var(--ink-mute)" }}
                  >
                    {row.synthid}
                  </td>
                  <td
                    className="py-5 pl-8 text-[15px] leading-[1.6]"
                    style={{ color: "var(--ink)" }}
                  >
                    {row.omnipulse}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-6 text-right">
          <a
            href="#contact"
            className="font-mono text-[12px] uppercase tracking-[0.12em] transition-opacity hover:opacity-60"
            style={{ color: "var(--ink-mute)" }}
          >
            Talk to us
          </a>
        </div>
      </div>
    </section>
  );
}
