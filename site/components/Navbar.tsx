"use client";

import Link from "next/link";

const navLinks = [
  { label: "Platform", href: "#platform" },
  { label: "Pricing", href: "#pricing" },
  { label: "Team", href: "#team" },
  { label: "Contact", href: "#contact" },
];

export default function Navbar() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 border-b"
      style={{
        height: 64,
        borderColor: "var(--rule)",
        backgroundColor: "var(--bg)",
      }}
    >
      <div className="flex items-center justify-between h-full max-w-[1280px] mx-auto px-6">
        <Link href="/" className="flex items-center gap-2 group">
          <span
            className="font-serif text-xl font-light"
            style={{ color: "var(--ink)" }}
          >
            <span style={{ color: "var(--accent)" }}>Ω</span>{" "}
            OmniPulse
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="font-mono text-[13px] uppercase tracking-[0.12em] transition-opacity hover:opacity-60"
              style={{ color: "var(--ink-mute)" }}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <a
            href="https://github.com/samvardhan03/Omnipulse"
            className="font-mono text-[12px] uppercase tracking-[0.12em] px-4 py-2 border transition-opacity hover:opacity-70"
            style={{ borderColor: "var(--rule)", color: "var(--ink)" }}
          >
            Docs ↗
          </a>
        </div>
      </div>
    </header>
  );
}
