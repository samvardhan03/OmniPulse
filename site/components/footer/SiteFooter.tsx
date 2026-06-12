import Link from "next/link";

const NAV_COLS = [
  {
    title: "Product",
    links: [
      { label: "Platform", href: "/#simulator" },
      { label: "Tiers", href: "/#platform" },
      { label: "Pricing", href: "/licensing" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Docs ↗", href: "https://github.com/samvardhan03/Omnipulse/#readme" },
      { label: "Changelog", href: "#" },
      { label: "GitHub ↗", href: "https://github.com/samvardhan03/Omnipulse" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/#team" },
      { label: "Contact", href: "mailto:shekhawatsamvardhan@gmail.com" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "License: AGPL-3.0 + Commercial", href: "https://github.com/samvardhan03/Omnipulse/blob/main/LICENSING.md" },
      { label: "Licensing", href: "/licensing" },
    ],
  },
];

export default function SiteFooter() {
  return (
    <footer className="pt-16 pb-12" style={{ borderTop: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8 mb-16">
          {/* Wordmark */}
          <div className="col-span-2 flex flex-col gap-2">
            <span className="font-serif text-[18px] font-light" style={{ color: "var(--ink)" }}>
              <span style={{ color: "var(--accent)" }}>Ω</span> OmniPulse
            </span>
            <span className="font-mono text-[11px]" style={{ color: "var(--ink-mute)" }}>
              Wavelet-scattering compliance infrastructure
            </span>
            <span className="font-mono text-[11px] mt-2" style={{ color: "var(--ink-mute)" }}>
              AGPL-3.0 + Commercial ·{" "}
              <a
                href="mailto:shekhawatsamvardhan@gmail.com"
                className="transition-opacity hover:opacity-60"
                style={{ color: "var(--ink)" }}
              >
                shekhawatsamvardhan@gmail.com
              </a>
            </span>
          </div>

          {/* Nav columns */}
          {NAV_COLS.map((col) => (
            <div key={col.title} className="flex flex-col gap-3">
              <p
                className="font-mono text-[11px] uppercase tracking-[0.16em]"
                style={{ color: "var(--ink-mute)" }}
              >
                {col.title}
              </p>
              {col.links.map((l) => {
                const isExternal = l.href.startsWith("http") || l.href.startsWith("mailto");
                return isExternal ? (
                  <a
                    key={l.label}
                    href={l.href}
                    className="font-mono text-[12px] transition-opacity hover:opacity-60"
                    style={{ color: "var(--ink)" }}
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link
                    key={l.label}
                    href={l.href}
                    className="font-mono text-[12px] transition-opacity hover:opacity-60"
                    style={{ color: "var(--ink)" }}
                  >
                    {l.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </div>

        <div
          className="pt-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
          style={{ borderTop: "1px solid var(--rule)" }}
        >
          <div className="flex flex-wrap gap-6">
            {[
              { label: "PyPI: omnipulse-agent", href: "https://pypi.org/project/omnipulse-agent/" },
              { label: "PyPI: omni-wst-core", href: "https://pypi.org/project/omni-wst-core/" },
              { label: "crates.io: vector-index", href: "https://crates.io/crates/vector-index" },
              { label: "GitHub: omnipulse", href: "https://github.com/samvardhan03/Omnipulse" },
            ].map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="font-mono text-[11px] transition-opacity hover:opacity-60"
                style={{ color: "var(--ink-mute)" }}
              >
                {l.label}
              </a>
            ))}
          </div>
          <span className="font-mono text-[11px]" style={{ color: "var(--ink-mute)" }}>
            © 2026 OmniPulse
          </span>
        </div>
      </div>
    </footer>
  );
}
