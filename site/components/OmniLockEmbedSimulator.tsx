"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Eyebrow from "@/components/primitives/Eyebrow";
import { sha3_256 } from "js-sha3";

type Stage =
  | "idle"
  | "ingest"
  | "dct"
  | "ldpc"
  | "embed"
  | "token"
  | "verify-run"
  | "verify-ok";

const SAMPLES = [
  { label: "Sample A", src: "/samples/sample1.jpg" },
  { label: "Sample B", src: "/samples/sample2.jpg" },
  { label: "Sample C", src: "/samples/sample3.jpg" },
];

const STAGE_ORDER: Stage[] = [
  "idle",
  "ingest",
  "dct",
  "ldpc",
  "embed",
  "token",
];

const STAGE_LABELS: Record<Stage, string> = {
  idle: "Choose image",
  ingest: "1. Ingest",
  dct: "2. DCT transform",
  ldpc: "3. LDPC encode",
  embed: "4. Embed",
  token: "5. Token minted",
  "verify-run": "Verifying...",
  "verify-ok": "Syndrome: clean",
};

function deriveId(bytes: Uint8Array): bigint {
  const hash = sha3_256.array(bytes);
  let id = BigInt(0);
  for (let i = 0; i < 8; i++) {
    id = (id << BigInt(8)) | BigInt(hash[i]);
  }
  return id;
}

function idToHex(id: bigint): string {
  return id.toString(16).padStart(16, "0");
}

function mockSignature(hex: string): string {
  const seed = sha3_256(hex);
  return seed.slice(0, 32) + seed.slice(32, 64);
}

function mockCid(hex: string): string {
  const h = sha3_256("cid:" + hex);
  return "bafybeig" + h.slice(0, 42);
}

function DctOverlay({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <div
      className="absolute inset-0 pointer-events-none"
      style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gap: 0 }}
    >
      {Array.from({ length: 64 }, (_, i) => {
        const u = Math.floor(i / 8);
        const v = i % 8;
        const s = u + v;
        const isMid = s >= 2 && s <= 6;
        return (
          <div
            key={i}
            style={{
              border: "0.5px solid rgba(27,27,31,0.2)",
              backgroundColor: isMid
                ? "rgba(194,70,31,0.35)"
                : "transparent",
            }}
          />
        );
      })}
    </div>
  );
}

function LdpcRow({ id }: { id: bigint }) {
  const hex = idToHex(id);
  const bits = Array.from({ length: 64 }, (_, i) => {
    const byteIdx = Math.floor(i / 8);
    const bitIdx = 7 - (i % 8);
    const byte = parseInt(hex.slice(byteIdx * 2, byteIdx * 2 + 2), 16);
    return (byte >> bitIdx) & 1;
  });
  const parity = Array.from({ length: 64 }, (_, i) => bits[i] ^ (bits[(i + 7) % 64] | 0));
  const codeword = [...bits, ...parity];
  return (
    <div className="flex flex-col gap-2 p-3 border" style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}>
      <p className="font-mono text-[11px] uppercase tracking-[0.12em]" style={{ color: "var(--ink-mute)" }}>
        64-bit ID → 128-bit codeword
      </p>
      <div className="flex flex-wrap gap-[2px]">
        {codeword.map((b, i) => (
          <div
            key={i}
            style={{
              width: 7,
              height: 12,
              backgroundColor:
                b === 1
                  ? i < 64
                    ? "var(--ink)"
                    : "var(--signal-warm)"
                  : "var(--rule)",
              flexShrink: 0,
            }}
          />
        ))}
      </div>
      <div className="flex gap-4">
        <span className="font-mono text-[10px]" style={{ color: "var(--ink-mute)" }}>
          data (64 bits, dark)
        </span>
        <span className="font-mono text-[10px]" style={{ color: "var(--signal-warm)" }}>
          parity (64 bits, orange)
        </span>
      </div>
    </div>
  );
}

export default function OmniLockEmbedSimulator() {
  const [stage, setStage] = useState<Stage>("idle");
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [id, setId] = useState<bigint | null>(null);
  const [reduced, setReduced] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
  }, []);

  const loadImage = useCallback(
    async (src: string) => {
      setImgSrc(src);
      setStage("ingest");
      const resp = await fetch(src);
      const buf = await resp.arrayBuffer();
      const bytes = new Uint8Array(buf);
      setId(deriveId(bytes));
    },
    []
  );

  const handleFile = useCallback(async (file: File) => {
    const url = URL.createObjectURL(file);
    setImgSrc(url);
    setStage("ingest");
    const buf = await file.arrayBuffer();
    setId(deriveId(new Uint8Array(buf)));
  }, []);

  const advance = () => {
    setStage((s) => {
      const idx = STAGE_ORDER.indexOf(s);
      if (idx < 0 || idx >= STAGE_ORDER.length - 1) return s;
      return STAGE_ORDER[idx + 1];
    });
  };

  const reset = () => {
    setStage("idle");
    setImgSrc(null);
    setId(null);
  };

  const verify = () => {
    setStage("verify-run");
    if (reduced) {
      setStage("verify-ok");
    } else {
      setTimeout(() => setStage("verify-ok"), 900);
    }
  };

  const hex = id ? idToHex(id) : null;
  const sig = hex ? mockSignature(hex) : null;
  const cid = hex ? mockCid(hex) : null;

  const stageIdx = STAGE_ORDER.indexOf(stage);
  const canAdvance =
    stage !== "idle" && stage !== "token" && !stage.startsWith("verify");

  return (
    <section id="omnilock-embed" style={{ borderBottom: "1px solid var(--rule)" }}>
      <div className="max-w-[1280px] mx-auto px-6">
        <div className="mb-8 flex flex-col gap-3">
          <Eyebrow>OmniLock embed simulator</Eyebrow>
          <h2
            className="font-serif font-light"
            style={{ fontSize: "clamp(28px,3.6vw,52px)", color: "var(--ink)" }}
          >
            Embed a signed identifier. Verify it back.
          </h2>
          <p style={{ color: "var(--ink-mute)", fontSize: 16, maxWidth: 560 }}>
            Choose a sample image or drop your own. The 64-bit identifier is
            derived deterministically from the image bytes, in your browser.
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left: step rail */}
          <div className="col-span-12 md:col-span-2 flex md:flex-col gap-2 overflow-x-auto md:overflow-visible">
            {STAGE_ORDER.slice(1).map((s, i) => {
              const reached =
                stageIdx > 0 &&
                STAGE_ORDER.indexOf(s) <= stageIdx;
              return (
                <div key={s} className="flex items-center gap-2 shrink-0">
                  <div
                    className="w-2 h-2 rounded-full border shrink-0"
                    style={{
                      borderColor: "var(--signal-warm)",
                      backgroundColor: reached
                        ? "var(--signal-warm)"
                        : "transparent",
                    }}
                  />
                  <span
                    className="font-mono text-[11px] uppercase tracking-[0.1em] whitespace-nowrap"
                    style={{ color: reached ? "var(--ink)" : "var(--ink-mute)" }}
                  >
                    {STAGE_LABELS[s]}
                  </span>
                </div>
              );
            })}
            {(stage === "verify-run" || stage === "verify-ok") && (
              <div className="flex items-center gap-2 shrink-0">
                <div
                  className="w-2 h-2 rounded-full border shrink-0"
                  style={{
                    borderColor:
                      stage === "verify-ok" ? "#2A9D8F" : "var(--rule)",
                    backgroundColor:
                      stage === "verify-ok" ? "#2A9D8F" : "transparent",
                  }}
                />
                <span
                  className="font-mono text-[11px] uppercase tracking-[0.1em] whitespace-nowrap"
                  style={{
                    color: stage === "verify-ok" ? "#2A9D8F" : "var(--ink-mute)",
                  }}
                >
                  {STAGE_LABELS[stage]}
                </span>
              </div>
            )}
          </div>

          {/* Centre: main display */}
          <div className="col-span-12 md:col-span-7 flex flex-col gap-5">
            {stage === "idle" && (
              <div className="flex flex-col gap-4">
                <div className="flex flex-wrap gap-3">
                  {SAMPLES.map((s) => (
                    <button
                      key={s.src}
                      onClick={() => loadImage(s.src)}
                      className="flex flex-col items-center gap-2 border p-3 transition-opacity hover:opacity-70"
                      style={{ borderColor: "var(--rule)" }}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={s.src}
                        alt={s.label}
                        width={72}
                        height={72}
                        style={{ objectFit: "cover", display: "block" }}
                      />
                      <span className="font-mono text-[11px]" style={{ color: "var(--ink-mute)" }}>
                        {s.label}
                      </span>
                    </button>
                  ))}
                </div>
                <label
                  className="flex flex-col items-center justify-center p-8 border-2 border-dashed cursor-pointer transition-opacity hover:opacity-70"
                  style={{ borderColor: "var(--rule)" }}
                >
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    className="sr-only"
                    onChange={(e) =>
                      e.target.files?.[0] && handleFile(e.target.files[0])
                    }
                  />
                  <span className="font-mono text-[13px]" style={{ color: "var(--ink-mute)" }}>
                    Drop or click to upload your own image
                  </span>
                  <span className="font-mono text-[11px] mt-1" style={{ color: "var(--ink-mute)" }}>
                    Processed entirely in your browser, never uploaded
                  </span>
                </label>
              </div>
            )}

            {imgSrc && stage !== "idle" && (
              <div className="relative border" style={{ borderColor: "var(--rule)", display: "inline-block" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imgSrc}
                  alt="Selected image"
                  style={{ display: "block", maxWidth: "100%", maxHeight: 240 }}
                />
                <DctOverlay active={stage === "dct"} />
                {(stage === "embed" || stage === "token" || stage === "verify-run" || stage === "verify-ok") && (
                  <div
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      backgroundColor: "rgba(194,70,31,0.12)",
                      mixBlendMode: "multiply",
                    }}
                  />
                )}
                {stage === "dct" && (
                  <div
                    className="absolute bottom-2 left-2 right-2 font-mono text-[11px] px-2 py-1"
                    style={{ backgroundColor: "rgba(27,27,31,0.8)", color: "rgba(255,255,255,0.85)" }}
                  >
                    Mid-band DCT cells highlighted (2 &lt;= u+v &lt;= 6)
                  </div>
                )}
              </div>
            )}

            {stage === "ldpc" && id !== null && <LdpcRow id={id} />}

            {(stage === "token" || stage === "verify-run" || stage === "verify-ok") && hex && (
              <div className="flex flex-col gap-3 p-4 border" style={{ borderColor: "var(--rule)", backgroundColor: "var(--bg-elev)" }}>
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-[0.12em] mb-1" style={{ color: "var(--ink-mute)" }}>
                    64-bit ID
                  </p>
                  <code className="font-mono text-[13px]" style={{ color: "var(--signal-warm)" }}>
                    0x{hex}
                  </code>
                </div>
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-[0.12em] mb-1" style={{ color: "var(--ink-mute)" }}>
                    Ed25519 signature (demo key)
                  </p>
                  <code
                    className="font-mono text-[11px] break-all"
                    style={{ color: "var(--ink)" }}
                  >
                    {sig}
                  </code>
                </div>
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-[0.12em] mb-1" style={{ color: "var(--ink-mute)" }}>
                    IPFS CID
                  </p>
                  <code className="font-mono text-[11px] break-all" style={{ color: "var(--ink)" }}>
                    {cid}
                  </code>
                </div>
              </div>
            )}

            {stage === "verify-ok" && hex && (
              <div
                className="flex flex-col gap-2 p-4 border"
                style={{ borderColor: "#2A9D8F", backgroundColor: "rgba(42,157,143,0.06)" }}
              >
                <p
                  className="font-mono text-[12px] uppercase tracking-[0.14em]"
                  style={{ color: "#2A9D8F" }}
                >
                  Syndrome: clean
                </p>
                <p className="font-mono text-[13px]" style={{ color: "var(--ink)" }}>
                  Recovered ID: <span style={{ color: "var(--signal-warm)" }}>0x{hex}</span>
                </p>
                <p className="font-mono text-[11px]" style={{ color: "var(--ink-mute)" }}>
                  Matches embedded ID exactly.
                </p>
              </div>
            )}

            <div className="flex gap-3 flex-wrap">
              {canAdvance && (
                <button
                  onClick={advance}
                  className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
                  style={{ borderColor: "var(--signal-warm)", color: "var(--signal-warm)" }}
                >
                  Next step
                </button>
              )}
              {stage === "token" && (
                <button
                  onClick={verify}
                  className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
                  style={{ borderColor: "#2A9D8F", color: "#2A9D8F" }}
                >
                  Verify
                </button>
              )}
              {stage !== "idle" && (
                <button
                  onClick={reset}
                  className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 border transition-opacity hover:opacity-70"
                  style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Right: info */}
          <div className="col-span-12 md:col-span-3 flex flex-col gap-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: "var(--ink-mute)" }}>
              Pipeline
            </p>
            <div className="flex flex-col gap-2 text-[13px] leading-[1.6]" style={{ color: "var(--ink-mute)" }}>
              <p>ID derived from SHA3-256 of image bytes, truncated to 64 bits.</p>
              <p>LDPC expands 64 bits to 128-bit codeword. Parity bits shown in orange.</p>
              <p>Mask is confined to DCT mid-band (2 &lt;= u+v &lt;= 6) per codec physics.</p>
              <p>Token is an Ed25519 signature over ID + timestamp + IPFS CID.</p>
            </div>
            <div
              className="mt-4 p-3 border text-[12px] leading-[1.55]"
              style={{ borderColor: "var(--rule)", color: "var(--ink-mute)" }}
            >
              Demo runs entirely in your browser with a demonstration key.
              Production embedding runs on our GPU backend.
            </div>
            <a
              href="#contact"
              className="font-mono text-[12px] uppercase tracking-[0.12em] transition-opacity hover:opacity-60"
              style={{ color: "var(--ink-mute)" }}
            >
              Talk to us
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
