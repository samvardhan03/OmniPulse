<div align="center">

# Ω OmniPulse

### Compliance & IP Infrastructure for the Generative Media Era

**Wavelet-scattering fingerprints. Zero-copy FFI. Memory-safe orchestration. MCP-native.**

[![PyPI — omnipulse-agent](https://img.shields.io/pypi/v/omnipulse-agent.svg?label=pypi%20omnipulse-agent&color=5BFFA0)](https://pypi.org/project/omnipulse-agent/)
[![PyPI — omni-wst-core](https://img.shields.io/pypi/v/omni-wst-core.svg?label=pypi%20omni-wst-core&color=5BFFA0)](https://pypi.org/project/omni-wst-core/)
[![crates.io — omni-ffi](https://img.shields.io/crates/v/omni-ffi.svg?label=crates%20omni-ffi&color=62E6FF)](https://crates.io/crates/omni-ffi)
[![crates.io — vector-index](https://img.shields.io/crates/v/vector-index.svg?label=crates%20vector-index&color=62E6FF)](https://crates.io/crates/vector-index)
[![crates.io — sliced-wasserstein](https://img.shields.io/crates/v/sliced-wasserstein.svg?label=crates%20sliced-wasserstein&color=62E6FF)](https://crates.io/crates/sliced-wasserstein)
[![License — AGPL-3.0 + Commercial](https://img.shields.io/badge/license-AGPL--3.0%2BCommercial-1B1B1F.svg)](./LICENSING.md)
[![Built with — Rust + C++/CUDA + Python](https://img.shields.io/badge/built%20with-Rust%20%2B%20C%2B%2B%2FCUDA%20%2B%20Python-1B1B1F.svg)]()

</div>

---

## This repository is the complete OmniPulse monorepo.

All four modules live here and ship to PyPI and crates.io independently.
This root lets you **read the architecture in one place** and jump to
whichever sub-package you need. See [`https://github.com/samvardhan03/Omnipulse`](https://github.com/samvardhan03/Omnipulse).

---

## Engineering outcomes (the headline numbers)

| Property | Outcome | Where it comes from |
|---|---|---|
| **End-to-end fingerprint latency** | < 40 ms for a 1-second 44.1 kHz audio clip on a single Hopper-class GPU | C++/CUDA `WSTEngine<HopperTag, J, Q>` on pre-pinned UVA pages |
| **Host ↔ device transfer throughput** | **15+ GB/s sustained DMA** on PCIe 4.0 x16 via Apache Arrow Plasma pages registered with `cudaHostRegister` | `cpp/wst_bridge.cu` — pinned, portable, no `cudaMemcpy` round-trip |
| **Python ↔ Rust handover cost** | **Zero-copy** — the f32 audio buffer is written once to POSIX shared memory and never re-serialized | `omnipulse-agent` → `omnipulse-rs` over a 28-char SHA3-256 hex shm name |
| **FFI boundary cost** | **Zero-marshalling** — `cxx` passes raw `u64` pointers across the C++↔Rust seam | `omni-ffi` — `unsafe extern "C++" fn run_wst_pipeline(input_plasma_ptr: u64, ...)` |
| **Memory safety** | RAII-guarded `WSTResult` ownership; `shm_unlink` is single-owner and idempotent | `OmniFfiKernel::WstResultGuard` in `omnipulse-rs`; `shm::read_and_unlink` |
| **Concurrency** | Lock-shared HNSW reads + bounded-time writes under `parking_lot::RwLock`; blocking kernel runs on `tokio::task::spawn_blocking` so stdio stays live | `ConcurrentHnsw<PointCloud, SlicedWasserstein>` |
| **Transport overhead** | Line-delimited JSON-RPC 2.0 over stdio — **no HTTP, no TLS, no socket setup** | rmcp `transport::stdio()` |
| **OS portability of segment names** | 28-char shm names fit the macOS `PSHMNAMLEN = 31` ceiling and every Linux kernel ever shipped | `hashlib.sha3_256(buf).digest()[:14].hex()` |

These are the operating points the architecture optimizes for. The
underlying math (analytic Morlet wavelet scattering, sliced
1-Wasserstein on empirical fingerprint distributions, HNSW indexing) is
explained in depth inside the per-module READMEs — this root keeps
the lens on *engineering outcomes*.

---

## Architecture at a glance

```
                         ┌──────────────────────────────────────────────┐
                         │   omnipulse-agent  (PyPI · Python 3.11+)    │
                         │   ──────────────────────────────────────    │
                         │   • Anthropic-driven cognitive router        │
                         │   • SharedMemoryManager (POSIX shm)          │
                         │   • MCPClient — line-delimited JSON-RPC 2.0  │
                         └────────────────────┬─────────────────────────┘
                                              │
                       28-char hex shm name   │   stdio pipes
                       (SHA3-256 digest[:14]) │   (one \n-terminated frame per call)
                                              ▼
                         ┌──────────────────────────────────────────────┐
                         │   omnipulse-rs  (crates.io · Rust workspace) │
                         │   ──────────────────────────────────────    │
                         │   • omnipulse-mcp binary  (rmcp stdio)       │
                         │   • vector-index  (concurrent HNSW)          │
                         │   • sliced-wasserstein  (SW₁ metric)         │
                         │   • shm_open + mmap + spawn_blocking         │
                         └────────────────────┬─────────────────────────┘
                                              │
                       u64 pinned-host ptr    │   cxx::bridge (zero-marshalling)
                       (UVA-registered page)  │
                                              ▼
                         ┌──────────────────────────────────────────────┐
                         │   omni-ffi  (crates.io · zero-copy bridge)   │
                         │   ──────────────────────────────────────    │
                         │   • cxx 1.0 — unsafe extern "C++"             │
                         │   • CPU path: cpp/wst_bridge_cpu.cpp          │
                         │   • CUDA path: cpp/wst_bridge_cuda.cpp        │
                         │     (links cudart + cufft)                    │
                         └────────────────────┬─────────────────────────┘
                                              │
                       raw float* / CUdeviceptr│
                                              ▼
                         ┌──────────────────────────────────────────────┐
                         │   omni-wst-core  (PyPI · C++/CUDA wheels)    │
                         │   ──────────────────────────────────────    │
                         │   • WSTEngine<HopperTag, J, Q>   (CUDA)       │
                         │   • build_cpu_morlet_bank + Radix-2 FFT (CPU) │
                         │   • Plasma cudaHostRegister                   │
                         └──────────────────────────────────────────────┘
```

Every arrow is **one** of: a 28-char shm name, a `\n`-terminated JSON
frame, a raw `u64` pointer, or a registered host page. No protobuf,
no gRPC, no HTTP, no JSON-over-network. That is the design.

---

## Modules — where each package lives

| Layer | Repo | Package | Quickstart |
|---|---|---|---|
| **DSP primitives** (C++/CUDA) | [`samvardhan03/Omnipulse`](https://github.com/samvardhan03/Omnipulse) — `omni-wst-core/` | `omni-wst-core` on PyPI | `pip install omni-wst-core` |
| **Zero-copy FFI bridge** (Rust ⇄ C++) | [`samvardhan03/Omnipulse`](https://github.com/samvardhan03/Omnipulse) — `omni-ffi/` | `omni-ffi` on crates.io | `cargo add omni-ffi` |
| **Rust orchestrator + indexes** | [`samvardhan03/Omnipulse`](https://github.com/samvardhan03/Omnipulse) — `omnipulse-rs/` | `vector-index`, `sliced-wasserstein` on crates.io; `omnipulse-mcp` binary | `cargo install omnipulse-mcp` |
| **Python agentic control plane** | [`samvardhan03/Omnipulse`](https://github.com/samvardhan03/Omnipulse) — `omnipulse-agent/` | `omnipulse-agent` on PyPI | `pip install omnipulse-agent` |

If you want the end-to-end demo, install both Python packages and
the Rust binary in the same environment, set `ANTHROPIC_API_KEY`, and
run `python -m omnipulse_agent.run --wav your.wav`.

---

## Try it (≈ 90 seconds)

```bash
# 1. The math engine (PyPI wheel — C++/CUDA inside)
pip install omni-wst-core

# 2. The Rust MCP orchestrator binary
cargo install omnipulse-mcp

# 3. The Python control plane (agentic layer)
pip install omnipulse-agent

# 4. Run the demo
export ANTHROPIC_API_KEY=sk-ant-...
python -m omnipulse_agent.run --wav your.wav
```

You will see the four-stage trace: ingest → shm pin → cxx bridge →
HNSW insert, with the 28-char SHA3 hex shm name printed at each
boundary.

---

## Repository layout (this showcase)

```
.
├── README.md                                ← you are here
├── omni-wst-core/                           ← C++/CUDA DSP engine
├── omni-ffi/                                ← cxx zero-copy FFI bridge
├── omnipulse-rs/                            ← Rust workspace (vector-index, sliced-wasserstein, omnipulse-mcp)
├── omnipulse-agent/                         ← Python agentic control plane
└── site/                                    ← Next.js marketing site (omnipulse.dev)
```

The vendored snapshots are kept **for reading only**. They lag the
canonical per-module repos slightly. Always clone the per-module repo
if you intend to build or contribute.

---

## Maintainers

- **Samvardhan Singh** — C++/CUDA DSP engine ([`omni-wst-core`](https://github.com/samvardhan03/Omnipulse)), the cxx FFI bridge ([`omni-ffi`](https://github.com/samvardhan03/Omnipulse)), and the PyPI agentic control plane ([`omnipulse-agent`](https://github.com/samvardhan03/Omnipulse)). Focus: automation engineering, AI/MLOps pipelines, engineering outcomes. [samvardhan.vercel.app](https://samvardhan.vercel.app/) · shekhawatsamvardhan@gmail.com
- **Yash Mishra** — Rust crates ([`vector-index`](https://github.com/samvardhan03/Omnipulse), [`sliced-wasserstein`](https://github.com/samvardhan03/Omnipulse)). Focus: concurrent systems, optimal transport, real-time indexing. [linkedin.com/in/mishra-yash2002](https://www.linkedin.com/in/mishra-yash2002/) · yash01012002@gmail.com
- **Phase 3 — Autonomous Agentic Control Plane** is **co-authored** by Samvardhan and Yash.

---

## Sister products

The OmniPulse scattering engine — omni-wst-core, omni-ffi, sliced-wasserstein, vector-index — also
powers two independent product surfaces built by the same team.

| Product | Domain | One-liner |
|---|---|---|
| [**ψ Vikshep**](https://vikshep.vercel.app) | Scientific compute | Wavelet scattering features for physics analyses — mass-decorrelated jet tagging, template-free BSM anomaly detection, rotation-invariant field inference. In pilot with the University of Edinburgh on Geant4-simulated ATLAS diboson data. |
| [**📡 Drift**](https://drift-site-livid.vercel.app) | Systematic alpha | Quantitative research platform — Cauchy wavelet features over log-returns, rank-transform IC/ICIR signal composition, Black-Litterman and HRP portfolio construction. 182 tests, Sharpe 0.70 on the 3-year synthetic HRP backtest. |

Same zero-copy core, same mathematical guarantees, completely different markets.

---

## License

Dual-licensed: **GNU AGPL-3.0** for open-source and research use (see [LICENSE](LICENSE)),
plus a **Commercial License** for proprietary or production deployments that cannot comply
with the AGPL-3.0 source-disclosure requirement (see [LICENSING.md](LICENSING.md)).

Contact shekhawatsamvardhan@gmail.com for commercial terms.

---

<div align="center">

If this repo is useful to you, **star it** so others can find it.

</div>
