# Contributing to OmniPulse

Contributions are welcome on the passive path, the kernels, and documentation.
The active embed path (OmniLock write side) requires engine artifacts that are
not in this repo; contributions there should be discussed with a maintainer first.

---

## Where contributions are welcome

- omni-wst-core: WST/JTFS kernel improvements, new wavelet families,
  build system fixes, additional platform support
- omni-ffi: bridge correctness, memory safety, build portability
- omnipulse-rs: vector-index (HNSW), sliced-wasserstein, MCP routing,
  shm naming, JSON-RPC correctness
- omnipulse-agent: MCP tool definitions, Python control plane, tests
- omni-lock-core: CUDA graph, C-ABI, build.rs, decoder correctness
  (note: kernel_ldpc.cu depends on a private H artifact; changes to
  the parity-check path need a maintainer to verify against the
  production matrix)
- site: copy, layout, accessibility, no new dependencies without discussion
- docs and specs: clarifications, corrections, new worked examples

## Where contributions are not accepted without prior discussion

- Changes to the OmniLock write path (embedder, Mixer architecture) that
  alter the embedding algorithm, since those changes affect the verify
  path compatibility
- New external dependencies in omni-lock-core or omni-lock-embed
- Any change to the 28-char shm naming convention (it is a security boundary)
- New features in omnipulse-mcp that add JSON-serialized tensors to the
  control plane (only shm names, ObjectIDs, and scalars cross the boundary)

---

## Code style

- Rust: `cargo fmt` and `cargo clippy --deny warnings` must pass
- C++: clang-format (Google style, column limit 100)
- Python: ruff format, ruff check (pyproject.toml settings)
- No emojis in code, comments, or commit messages
- No invented benchmarks: if a number is a budget or design target, say so
  explicitly ("designed for X" or "budget: X", not "achieves X")
- Fail loudly: missing artifacts, missing env vars, and bad inputs must
  produce a descriptive multi-line error and a non-zero exit code.
  No silent fallbacks, no stub kernels, no CPU mocks of CUDA paths

---

## FFI rules (non-negotiable)

Two FFI families, never unified:

1. WST FFI: cxx::bridge between omni-ffi (Rust) and omni-wst-core (C++).
2. OmniLock FFI: hand-written extern "C" ABI v3 in omni-lock-core.

They meet only in omnipulse-mcp routing code (Rust), never in C++. Run
`bash scripts/check_ffi_separation.sh` before submitting a PR that touches
either FFI seam. The CI gate runs this check automatically.

---

## Pull request process

1. Fork the repo and create a branch from main.
2. Run the full check suite:
   ```
   bash scripts/check_ffi_separation.sh
   bash scripts/check_no_secrets.sh
   cargo test --workspace
   ```
3. The passive path must build and its tests must pass with no private
   artifacts (OMNIPULSE_ENGINE_DIR unset). If your change touches the
   active path, document that the test requires engine artifacts.
4. Keep PRs focused. One concern per PR.
5. Commit messages: imperative mood, present tense, no trailing period.

---

## Reporting issues

Open a GitHub issue. For security issues that should not be public, email
shekhawatsamvardhan@gmail.com directly.
