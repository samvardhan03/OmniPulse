import Eyebrow from "@/components/primitives/Eyebrow";
import { FOUNDERS, COAUTHORED_NOTE } from "./founders.data";

export default function FoundersCreatorsBios() {
  return (
    <section id="team" style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>Founders &amp; creators</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            The people behind the platform
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FOUNDERS.map((f) => (
            <div key={f.name}>
              <div
                className="border flex flex-col gap-5 h-full"
                style={{ borderColor: "var(--rule)", padding: 32 }}
              >
                <div className="flex flex-col gap-1">
                  <p
                    className="font-mono text-[11px] uppercase tracking-[0.18em]"
                    style={{ color: "var(--accent)" }}
                  >
                    {f.eyebrow}
                  </p>
                  <h3
                    className="font-serif font-light text-[28px] leading-tight"
                    style={{ color: "var(--ink)" }}
                  >
                    {f.name}
                  </h3>
                  <p className="text-[14px]" style={{ color: "var(--ink-mute)" }}>
                    {f.role}
                  </p>
                </div>

                <p className="text-[15px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
                  {f.focus}
                </p>

                <div className="flex flex-col gap-1">
                  {f.portfolio && (
                    <a
                      href={f.portfolio}
                      className="font-mono text-[12px] transition-opacity hover:opacity-60"
                      style={{ color: "var(--ink)" }}
                    >
                      {f.portfolio.replace("https://", "")}
                    </a>
                  )}
                  {f.linkedin && (
                    <a
                      href={f.linkedin}
                      className="font-mono text-[12px] transition-opacity hover:opacity-60"
                      style={{ color: "var(--ink)" }}
                    >
                      {f.linkedin.replace("https://", "")}
                    </a>
                  )}
                  {"github" in f && f.github && (
                    <a
                      href={f.github as string}
                      className="font-mono text-[12px] transition-opacity hover:opacity-60"
                      style={{ color: "var(--ink)" }}
                    >
                      {(f.github as string).replace("https://", "")}
                    </a>
                  )}
                  {"email" in f && f.email && (
                    <a
                      href={`mailto:${f.email}`}
                      className="font-mono text-[12px] transition-opacity hover:opacity-60"
                      style={{ color: "var(--ink)" }}
                    >
                      email: {f.email}
                    </a>
                  )}
                </div>

                <div
                  className="pt-4 border-t flex flex-col gap-2"
                  style={{ borderColor: "var(--rule)" }}
                >
                  <p
                    className="font-mono text-[11px] uppercase tracking-[0.12em]"
                    style={{ color: "var(--ink-mute)" }}
                  >
                    Maintains
                  </p>
                  {f.maintains.map((m) => (
                    <a
                      key={m.label}
                      href={m.href}
                      className="flex items-baseline gap-3 transition-opacity hover:opacity-70"
                    >
                      <code
                        className="font-mono text-[13px]"
                        style={{ color: "var(--ink)" }}
                      >
                        {m.label}
                      </code>
                      <span
                        className="font-mono text-[11px]"
                        style={{ color: "var(--ink-mute)" }}
                      >
                        - {m.note}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        <aside
          className="col-span-12 mt-4 border-t pt-6 font-mono text-[13px]"
          style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
        >
          Co-authored:{" "}
          <strong style={{ color: "var(--ink)" }}>
            Phase 3: The Agentic Control Plane
          </strong>{" "}
          is jointly maintained by <em>Samvardhan</em> and <em>Yash</em> across{" "}
          <code>omnipulse-agent</code> (Python) and the{" "}
          <code>omnipulse-mcp</code> server in <code>omnipulse-rs</code>.
        </aside>
      </div>
    </section>
  );
}
