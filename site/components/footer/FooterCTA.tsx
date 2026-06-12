import Eyebrow from "@/components/primitives/Eyebrow";

export default function FooterCTA() {
  return (
    <section style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="flex flex-col gap-6 max-w-[640px]">
          <Eyebrow>Get started</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            Ready to integrate the fingerprint plane?
          </h2>
          <p className="text-[17px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
            Start with the open-source modules. The core is AGPL-3.0 + Commercial —
            enterprise production is a conversation.
          </p>
          <div className="flex flex-wrap gap-4">
            <a
              href="https://github.com/samvardhan03/Omnipulse"
              className="font-mono text-[13px] uppercase tracking-[0.12em] px-6 py-3 border transition-opacity hover:opacity-70"
              style={{ borderColor: "var(--ink)", color: "var(--ink)" }}
            >
              View the Showcase Repo →
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
