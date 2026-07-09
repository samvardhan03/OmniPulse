# OmniPulse

OmniPulse is a media provenance platform for creators and rights organizations.
It pairs two complementary verification modes on a shared substrate: OmniLock
embeds a cryptographically signed 64-bit identifier into a video or image at
creation (active, write-path), and OmniPulse computes a deterministic
wavelet-scattering fingerprint that matches any derivative without cooperation
at creation (passive, read-path). Both layers write to the same signed ledger
and run on the same CUDA/Rust/Python substrate. The verify path is fixed-operator
mathematics -- a linear parity check and an HNSW nearest-neighbor query -- so
the verdict does not depend on a black-box service or on this team being
available.

---

## Architecture

```
omnipulse-agent  (Python, MCP control plane)
      |
      | 28-char shm name (SHA3-256 digest[:14].hex(), fits macOS PSHMNAMLEN=31)
      | stdio pipes (newline-delimited JSON-RPC 2.0, no HTTP)
      v
omnipulse-rs  (Rust workspace: omnipulse-mcp, vector-index, sliced-wasserstein)
      |
      | u64 pinned host pointer (UVA-registered, zero-copy across the seam)
      | cxx::bridge (zero-marshalling, no intermediate serialization)
      v
omni-ffi  (Rust/C++ bridge crate, WST FFI family)
      |
      | raw float* / CUdeviceptr
      v
omni-wst-core  (C++/CUDA: WSTEngine, Morlet bank, Plasma host register)

     AND separately, via hand-written extern "C" ABI v3 (OmniLock FFI family):

omni-lock-core  (Rust inference crate, omnilock_backend C-ABI, CUDA graph)
omni-lock-embed (Python: embedder, extractor, Sum-Product decoder)
```

### Two FFI families

There are two FFI seams and they never merge:

1. WST FFI (passive path): `cxx::bridge` between `omni-ffi` (Rust) and
   `omni-wst-core` (C++/CUDA). The bridge carries UVA-registered host
   pointers and raw `u64` values; no JSON, no protobuf, no copy.

2. OmniLock FFI (active path): hand-written `extern "C"` ABI v3 in
   `omni-lock-core/include/omnilock_ffi.h`. Functions:
   `omnilock_backend_create`, `omnilock_backend_destroy`,
   `omnilock_capture_inference_graph`, `omnilock_launch_inference_graph`.
   Status codes: OK=0, ERR_NULL_PTR=-1 through ERR_NOT_INITIALIZED=-5.
   The two FFI families meet only in the Rust routing code of `omnipulse-mcp`,
   never in C++.

### Why 28 characters for the shm name

`hashlib.sha3_256(buf).digest()[:14].hex()` produces a 28-character hex string.
macOS caps POSIX shared-memory names at `PSHMNAMLEN = 31` bytes including the
leading `/`. 28 characters plus the prefix slash uses 29 bytes and fits every
macOS and Linux kernel version without conditional logic. The name is a content
digest, not a counter, so two identical buffers get the same name and the
second shm_open returns the existing segment without an extra copy.

---

## What is public and what is not

**Rule:** fixed operators are public; trained artifacts and secrets are private.

Public (this repo):
- All WST/JTFS kernels, Sliced-Wasserstein, HNSW, the cxx bridge
- The extern "C" ABI v3 and the CUDA graph capture code in omni-lock-core
- The Sum-Product decoder algorithm in omni-lock-embed (ldpc_decode_soft)
- The embedder and extractor architecture (network definitions, no weights)
- omnipulse-agent, omnipulse-mcp, the site, all specs

Private (github.com/samvardhan03/omni):
- The production LDPC parity-check matrix H and the generator that emits it.
  Publishing H turns the verify rule into a forgery target; the digest constant
  LDPC_H_SHA3_DIGEST is compiled into the public tree as a tamper check without
  revealing the matrix.
- Trained Mixer weights and the training procedure. The Mixer shapes the
  residual mask on the write path; publishing weights gives an adversary a
  warm start on a targeted attack.
- The Ed25519 issuer key and registry schema (secrets by definition).

The verify path (passive fingerprint, active parity check + signature) uses
only fixed operators and is fully inspectable in this repo. The write path
uses trained shaping that stays private. This is a coherent split: anyone
can audit the verification rule; the embedding quality is our moat.

---

## Quickstart: passive fingerprint path (no private artifacts needed)

The passive path -- fingerprint a media file and insert it into the HNSW index
-- builds and runs from this repo alone. The active embed/decode path requires
engine artifacts from the private repo; it fails loudly with instructions if
those artifacts are absent (see omni-lock-core/build.rs and
omni-lock-embed/omni_lock/ldpc.py).

### Requirements (passive path)

- Python 3.11+
- Rust 1.78+ (`rustup show`)
- C++17 compiler
- CUDA Toolkit 11.8+ for the GPU path; the CPU Morlet fallback (`--features omni-ffi`)
  works without CUDA

### Steps

```bash
git clone https://github.com/samvardhan03/Omnipulse.git
cd Omnipulse

# 1. Python packages
pip install omni-wst-core omnipulse-agent

# 2. Rust MCP orchestrator (passive path, CPU Morlet fallback if no CUDA)
cargo build -p omnipulse-mcp --features omni-ffi

# 3. Fingerprint a WAV file
export ANTHROPIC_API_KEY=sk-ant-...
python -m omnipulse_agent.run --wav your.wav
```

You will see the four-stage trace: ingest, shm pin (28-char SHA3 name printed),
cxx bridge, HNSW insert.

---

## Status

| Property | Status | Note |
|---|---|---|
| Passive fingerprint (audio) | Implemented | WSTEngine, Morlet bank, HNSW, SW1 |
| Passive fingerprint (image/video) | Implemented | Same kernel family, different input shape |
| Active embed (OmniLock write path) | Implemented, not production-hardened | Requires engine artifacts; H not yet fixed-seed |
| Active verify (OmniLock read path) | Implemented | Sum-Product decoder, parity check |
| Ed25519 registry ledger | Proposed | Infrastructure wired; issuer key not provisioned |
| 60 FPS real-time embed | Budget, not measured | 38 ms/frame kernel budget on H100; not benchmarked end to end |
| court-report export | Proposed | VPD designed, not implemented |

---

## Repository layout

```
omni-wst-core/        C++/CUDA DSP engine (WSTEngine, Morlet bank)
omni-ffi/             cxx zero-copy FFI bridge (WST FFI family)
omnipulse-rs/         Rust workspace
  crates/
    omnipulse-mcp/    MCP binary (stdio JSON-RPC, HNSW, SW1)
    vector-index/     concurrent HNSW
    sliced-wasserstein/ SW1 metric
    omni-lock-core/   OmniLock C-ABI v3, CUDA graph, build.rs (OmniLock FFI family)
omni-lock-embed/      Python: embedder, extractor, decoder, Mixer architecture
omnipulse-agent/      Python MCP control plane
site/                 Next.js marketing site
scripts/              FFI separation check, secrets check
```

---

## License

AGPL-3.0 for open-source and research use. Commercial license for production
deployments that cannot comply with AGPL source-disclosure requirements.
Contact shekhawatsamvardhan@gmail.com for commercial terms.

---

## Maintainers

Samvardhan Singh -- systems, signal processing, CUDA substrate.
samvardhan.vercel.app / shekhawatsamvardhan@gmail.com

Yash Mishra -- scattering research and the passive engine.
linkedin.com/in/mishra-yash2002

Shreyansh Jain -- agentic systems and the active layer (OmniLock).
shreyanshjain05.vercel.app / github.com/shreyanshjain05

---

## Contributing

See CONTRIBUTING.md.
