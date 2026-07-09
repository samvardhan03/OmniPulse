const modules = [
  { name: "omni-wst-core", version: "0.1", channel: "PyPI" },
  { name: "omni-ffi", version: "0.1", channel: "crate" },
  { name: "omni-hnsw", version: "0.1", channel: "crate" },
  { name: "omni-sw", version: "0.1", channel: "crate" },
  { name: "omnipulse-agent", version: "0.1", channel: "PyPI" },
];

const COLUMNS = [
  {
    label: "What it is",
    body: "The identifier lives inside the media, not in a sidecar a re-upload can strip. Verification is deterministic mathematics, not a black-box service.",
  },
  {
    label: "Why it is different",
    body: "Two engines, one substrate: OmniLock writes a 64-bit LDPC watermark. OmniPulse reads WST/JTFS scattering coefficients. Neither requires a cloud call to verify.",
  },
  {
    label: "Who it is for",
    body: "Independent creators, studios, and rights organizations who need to license, track, and monetize their work without ceding the record to a platform.",
  },
];

export default function HeroValueStrip() {
  return (
    <section style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6 py-14">
        <div className="grid grid-cols-12 gap-6">
          {/* Three value columns */}
          {COLUMNS.map((col) => (
            <div key={col.label} className="col-span-12 md:col-span-3 flex flex-col gap-3">
              <p
                className="font-mono text-[11px] uppercase tracking-[0.16em]"
                style={{ color: "var(--ink-mute)" }}
              >
                {col.label}
              </p>
              <p className="text-[15px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
                {col.body}
              </p>
            </div>
          ))}

          {/* Module stack */}
          <div className="col-span-12 md:col-span-3 flex flex-col gap-3">
            <p
              className="font-mono text-[11px] uppercase tracking-[0.16em]"
              style={{ color: "var(--ink-mute)" }}
            >
              Module stack
            </p>
            <div
              className="border p-4 flex flex-col gap-3"
              style={{ borderColor: "var(--rule)" }}
            >
              {modules.map((m) => (
                <div key={m.name} className="flex items-baseline justify-between gap-4">
                  <code className="font-mono text-[12px]" style={{ color: "var(--ink)" }}>
                    {m.name}
                  </code>
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[11px]" style={{ color: "var(--ink-mute)" }}>
                      {m.version}
                    </span>
                    <span
                      className="font-mono text-[9px] uppercase tracking-[0.1em] px-1.5 py-0.5 border"
                      style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
                    >
                      {m.channel}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
