export const FOUNDERS = [
  {
    name: "Samvardhan Singh",
    eyebrow: "ARCHITECT, APPLIED AI / MLOPS",
    role: "Systems, signal processing, and the CUDA substrate",
    focus: "Automation engineering, AI/MLOps pipelines, engineering outcomes.",
    maintains: [
      { label: "omni-wst-core", note: "C++/CUDA DSP engine", href: "https://pypi.org/project/omni-wst-core/" },
      { label: "omni-ffi", note: "cxx zero-copy FFI bridge", href: "https://crates.io/crates/omni-ffi" },
      { label: "omnipulse-agent", note: "Python agentic control plane (PyPI)", href: "https://pypi.org/project/omnipulse-agent/" },
    ],
    portfolio: "https://samvardhan.vercel.app/",
    github: "https://github.com/samvardhan03",
    email: "shekhawatsamvardhan@gmail.com",
    linkedin: undefined as string | undefined,
  },
  {
    name: "Yash Mishra",
    eyebrow: "ARCHITECT, SYSTEMS / OPTIMAL TRANSPORT",
    role: "Scattering research and the passive engine",
    focus: "Concurrent systems, optimal transport, real-time indexing logic.",
    maintains: [
      { label: "vector-index", note: "Concurrent HNSW", href: "https://crates.io/crates/vector-index" },
      { label: "sliced-wasserstein", note: "SW1 distance metric for HNSW", href: "https://crates.io/crates/sliced-wasserstein" },
    ],
    portfolio: undefined as string | undefined,
    github: undefined as string | undefined,
    linkedin: "https://www.linkedin.com/in/mishra-yash2002/",
    email: "yash01012002@gmail.com",
  },
  {
    name: "Shreyansh Jain",
    eyebrow: "ENGINEER, AGENTIC SYSTEMS / ACTIVE LAYER",
    role: "Agentic systems and the active layer (OmniLock)",
    focus: "GenAI and agentic-systems engineer; research publications and open-source Python packages.",
    maintains: [
      { label: "omni-lock-core", note: "CUDA inference crate (C-ABI v3)", href: "https://github.com/shreyanshjain05" },
      { label: "omni-lock-embed", note: "PyTorch embedder", href: "https://github.com/shreyanshjain05" },
    ],
    portfolio: "https://shreyanshjain05.vercel.app",
    github: "https://github.com/shreyanshjain05",
    linkedin: "https://www.linkedin.com/in/shreyanshjain05/",
    email: undefined as string | undefined,
  },
] as const;

export const COAUTHORED_NOTE = {
  text: "Phase 3 (the Autonomous Agentic Control Plane) is co-authored by Samvardhan and Yash.",
  cite: ["omnipulse-agent", "omnipulse-mcp"],
} as const;
