"""
transient_wst
=============
Enterprise-grade Wavelet Scattering Transform (WST) engine for non-stationary
time-series data.  Designed as a self-contained, MCP-compatible scientific
processing backend for the Agentic-Wavelet Foundation Pipeline.

This package is **domain-agnostic** — it processes any 1-D time-series
(EEG, FRB, seismic, financial) through a cascaded Kymatio scattering
transform with optional PCA dimensionality reduction.

Public API
----------
>>> from transient_wst import WaveletScatteringExtractor, ScatteringResult
>>> extractor = WaveletScatteringExtractor(J=8, Q=(8, 1))
>>> result = extractor.transform(signal_array)
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__: str = version("transient-wst")
except PackageNotFoundError:  # running from source without install
    __version__ = "0.0.0.dev"

# ── Public surface ─────────────────────────────────────────────────────────────
from transient_wst.core import WaveletScatteringExtractor, ScatteringResult
from transient_wst.reduction import PCAReducer
from transient_wst.io import load_npy_directory, save_arrays
from transient_wst.utils import compute_snr_db, detect_outlier_paths

__all__ = [
    "WaveletScatteringExtractor",
    "ScatteringResult",
    "PCAReducer",
    "load_npy_directory",
    "save_arrays",
    "compute_snr_db",
    "detect_outlier_paths",
    "__version__",
]