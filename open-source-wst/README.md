# Vikshep: High-Performance Wavelet Scattering Primitives

<div align="center">
  <p><strong>Vectorized Invariant Kernels for Scattering & High-performance Extraction Pipelines</strong></p>
  <img src="https://img.shields.io/badge/License-Apache_2.0-teal.svg" alt="License: Apache 2.0">
  <img src="https://img.shields.io/badge/Commercial_License-OmniPulse_Enterprise-indigo.svg" alt="License: Commercial">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/CUDA-11.8%2B-green.svg" alt="CUDA 11.8+">
</div>

---

## 🔬 Overview & Mathematical Foundation

**Vikshep** is a high-performance, domain-agnostic mathematical engine for computing the **Wavelet Scattering Transform (WST)** of non-stationary 1-D time-series data. It is engineered to extract robust structural features from environments with extreme noise floors (e.g., high-frequency trading tick data, gravitational wave interferometry, and high-density EEG arrays).

Traditional Fourier analysis fails on non-stationary transients due to a fundamental lack of temporal localization. Vikshep solves this by implementing a deep, non-linear cascaded filter bank. 

### The Scattering Cascade

The WST constructs a translation-invariant signal representation through an iterative process of wavelet convolutions and complex modulus non-linearities:

1. **Zeroth-Order (Local Average):** 
   $$S_0 x(t) = x * \phi(t)$$
   A simple low-pass filter $\phi(t)$ that extracts the invariant baseline.

2. **First-Order (Scalogram Envelope):**
   $$S_1 x(t, \lambda_1) = |x * \psi_{\lambda_1}| * \phi(t)$$
   The signal $x(t)$ is convolved with an analytic Morlet wavelet $\psi_{\lambda_1}$ at center frequency $\lambda_1$. The complex modulus $| \cdot |$ acts as a non-linearity (demodulation), extracting the instantaneous amplitude envelope. Finally, it is smoothed by $\phi(t)$. This captures the energy present in the frequency band $\lambda_1$.

3. **Second-Order (Transient Modulation):**
   $$S_2 x(t, \lambda_1, \lambda_2) = ||x * \psi_{\lambda_1}| * \psi_{\lambda_2}| * \phi(t)$$
   The *envelope* from the first stage is convolved again with a lower-frequency wavelet $\psi_{\lambda_2}$, capturing transient cross-frequency modulations (e.g., amplitude bursts occurring within specific carrier frequency bands). 

### Lipschitz Stability & Deformation Invariance

Because the Morlet filter bank is carefully constructed such that the peak $\ell_1$ norm of the wavelets satisfies $\|\psi_{\lambda}\|_1 \le 0.98$, the transform is **provably contractive**. 

The Lipschitz constant of the cascade is strictly bounded:
$$\|Sx - Sy\|_2 \;\leq\; (0.98)^m \cdot \|x - y\|_2$$

where $m$ is the scattering depth. This mathematical guarantee ensures that the feature representation is stable against adversarial noise perturbations and time-warping deformations—essential properties for downstream Transformer or AI agent ingestion.

---

## ⚡ The Engine Architecture

Vikshep ships a **Zero-Copy C++/CUDA kernel** for extreme high-throughput processing, alongside a mathematically rigorous **CPU fallback** built on a Radix-2 Cooley-Tukey FFT with unitary normalization.

**Absolute design constraints:** There are zero mocks. There are no hardcoded scalograms. Every execution path performs the true mathematical transform.

### Detailed Directory Structure

```text
open-source-wst/
├── CMakeLists.txt                 ← CMake build configuration (detects CUDA, falls back to CPU)
├── pyproject.toml                 ← PEP 621 package metadata & scikit-build-core config
│
├── cpp/                           ← C++/CUDA High-Performance Engine
│   ├── wst_kernel.cuh             ← GPU templates: WSTEngine<HopperTag, J, Q> 
│   ├── jtfs_kernel.cuh            ← GPU Joint Time-Frequency Scattering kernels
│   ├── cpu_wst_engine.h           ← CPU fallback: Radix-2 FFT Morlet scattering cascade
│   ├── memory_staging.cuh/cu      ← Zero-copy Arrow/Numpy buffer management
│   ├── wst_bindings.cu            ← pybind11 Python extension bridging
│   └── wst_bridge.h/cu            ← Shared library FFI for Rust enterprise orchestrator
│
└── src/vikshep/                   ← Python API & Agentic Protocols
    ├── __init__.py                
    ├── core.py                    ← `NativeWSTExtractor` & `WaveletScatteringExtractor`
    ├── mcp_server.py              ← Model Context Protocol (FastMCP) tool definitions
    ├── reduction.py               ← `PCAReducer` for manifold dimension reduction
    ├── foundation.py              ← Time-Frequency Consistency (TF-C) PyTorch stub
    ├── io.py                      ← .npy tensor I/O
    └── utils.py                   ← SNR & anomaly threshold heuristics
```

---

## 🚀 Installation & Usage

### 1. PyPI Install (Standard)
```bash
pip install vikshep
```
*Note: The PyPI wheel will automatically detect if NVIDIA CUDA libraries are available and enable GPU acceleration. Otherwise, it compiles the CPU-only Radix-2 FFT backend.*

### 2. From Source
```bash
git clone https://github.com/samvardhan03/Viskshep.git
cd Viskshep/open-source-wst
pip install -e ".[dev]"
```

### Quick Start Example

```python
import numpy as np
from vikshep import NativeWSTExtractor, PCAReducer

# 1. Initialize the C++/CUDA Engine (J=8 scales, Q=16 wavelets/octave)
engine = NativeWSTExtractor(J=8, Q=16, depth=2)

# 2. Ingest raw non-stationary signal (e.g., noisy EEG or Tick Data)
signal = np.random.randn(4096).astype(np.float32)

# 3. Compute the Wavelet Scattering Fingerprint
coefficients = engine.fingerprint(signal)
print(f"Scattering Paths Shape: {coefficients.shape}")

# 4. Reduce dimensionality for Transformer ingestion (retain 95% variance)
reducer = PCAReducer(variance_threshold=0.95)
# Note: In practice, provide a batch tensor (B, P, T) to fit_transform
```

---

## Model Context Protocol (MCP)

Vikshep functions as an autonomous tool for Agentic AI workflows via the Model Context Protocol.

Start the stdio transport server:
```bash
vikshep-server
```
This exposes the `execute_wst` tool to orchestrators (like LangChain or custom Bun backends), allowing the AI to autonomously ingest `.npy` directories, configure hyper-parameters $(J, Q)$, compute WSTs, apply PCA reduction, and receive structured JSON metadata (SNR, null counts, variance anomalies) to gate data quality.

---

## ⚖️ Dual Licensing Model

Vikshep operates under a dual-licensing framework to support both open scientific research and highly-scaled proprietary enterprise integrations.

1. **Open Source Research Tier (Apache 2.0)**
   - Includes the core Python API, the full C++/CUDA math engine (`wst_kernel.cuh`, `cpu_wst_engine.h`), and the Model Context Protocol (MCP) server.
   - Ideal for independent researchers, academic labs, and open-source applications.
   - *License:* See [`LICENSE`](LICENSE) for Apache 2.0 details.

2. **Vikshep Enterprise / Commercial License**
   - **Vikshep** is our proprietary enterprise SaaS tier that utilizes Vikshep as its mathematical backend.
   - OmniPulse deployments include high-throughput Rust-based orchestration clusters, Zero-Copy Arrow Plasma memory fabrics, cryptographic IPFS licensing, HNSW vector database integrations, and proprietary data ingestion pipelines (e.g., FIX protocols for HFT).
   - *Contact:* For laboratory exascale deployments, clinical pipelines, or enterprise commercial integration, please contact [shekhawatsamvardhan@gmail.com](mailto:shekhawatsamvardhan@gmail.com).

Part of the [Viskshep](https://github.com/samvardhan03/Viskshep) monorepo.
