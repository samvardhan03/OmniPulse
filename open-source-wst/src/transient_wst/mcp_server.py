"""
transient_wst.mcp_server
========================
Model Context Protocol (MCP) server exposing the Wavelet Scattering
Transform pipeline as a tool callable by the TypeScript agentic orchestrator.

Uses the ``FastMCP`` high-level API from the official ``mcp`` Python SDK.
The server communicates over **stdio** transport, spawned as a subprocess
by the Bun-based MCP client.

Tool surface
------------
``execute_wst``
    Ingest a directory of ``.npy`` time-series arrays, apply the cascaded
    WST via Kymatio, optionally reduce via PCA, save outputs, and return
    structured JSON diagnostics (SNR, variance, null count).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from mcp.server.fastmcp import FastMCP

from transient_wst.core import WaveletScatteringExtractor
from transient_wst.io import load_npy_directory, save_arrays
from transient_wst.reduction import PCAReducer
from transient_wst.utils import detect_outlier_paths

logger = logging.getLogger(__name__)

# ── MCP Server instance ───────────────────────────────────────────────────
mcp = FastMCP("transient-wst")


@mcp.tool()
def execute_wst(
    input_directory: str,
    output_directory: str,
    sampling_rate: float = 256.0,
    j_scale: int = 8,
    q1: int = 8,
    q2: int = 1,
    apply_pca: bool = True,
    pca_variance: float = 0.95,
) -> str:
    """Execute the cascaded Wavelet Scattering Transform on .npy files.

    Loads all .npy arrays from ``input_directory``, runs the Kymatio
    Scattering1D transform with the specified hyperparameters, optionally
    applies PCA dimensionality reduction, saves results to
    ``output_directory``, and returns diagnostic metadata as JSON.

    Args:
        input_directory: Path to folder containing input .npy files (shape B×T).
        output_directory: Path to save transformed .npy outputs.
        sampling_rate: Signal sampling frequency in Hz.
        j_scale: Maximum scattering scale J (power-of-two window, 1–16).
        q1: Wavelets per octave for the first-order filter bank (≥1).
        q2: Wavelets per octave for the second-order filter bank (≥1).
        apply_pca: Whether to apply PCA reduction after scattering.
        pca_variance: Cumulative variance threshold for PCA (0–1).

    Returns:
        JSON string containing diagnostic metadata:
        ``{"snr_db", "variance", "null_count", "n_files_processed",
        "output_shape", "outlier_paths", "pca_applied", "pca_components"}``.
    """
    # ── 1. Build the extractor ──────────────────────────────────────────
    extractor = WaveletScatteringExtractor(
        J=j_scale,
        Q=(q1, q2),
        sampling_rate=sampling_rate,
    )

    # ── 2. Load input data ──────────────────────────────────────────────
    file_pairs = load_npy_directory(input_directory)

    all_snr: list[float] = []
    all_null: list[int] = []
    all_variance: list[list[float]] = []
    outputs: dict[str, np.ndarray] = {}

    # ── 3. Transform each file ──────────────────────────────────────────
    for filename, signal in file_pairs:
        result = extractor.transform(signal, meta={"source": filename})

        all_snr.append(result.snr_db)
        all_null.append(result.null_count)
        all_variance.append(result.variance.tolist())

        stem = Path(filename).stem
        outputs[f"{stem}_wst"] = result.coefficients

    # ── 4. Optional PCA reduction ───────────────────────────────────────
    pca_components: int | None = None
    if apply_pca and outputs:
        reducer = PCAReducer(variance_threshold=pca_variance)
        reduced_outputs: dict[str, np.ndarray] = {}
        for name, coeffs in outputs.items():
            # Sanitize NaNs and Infs so PCA doesn't crash on extreme anomalies
            clean_coeffs = np.nan_to_num(coeffs, nan=0.0, posinf=0.0, neginf=0.0)
            reduced = reducer.fit_transform(clean_coeffs)
            reduced_outputs[f"{name}_pca"] = reduced
            pca_components = reducer.n_components
        outputs.update(reduced_outputs)

    # ── 5. Save outputs ─────────────────────────────────────────────────
    save_arrays(outputs, output_directory)

    # ── 6. Compute aggregate diagnostics ────────────────────────────────
    if all_variance:
        # nanmean avoids NaN poisoning the entire array
        mean_variance = np.nanmean(all_variance, axis=0).tolist()
        mean_variance = [0.0 if np.isnan(v) else v for v in mean_variance]
    else:
        mean_variance = []

    outlier_paths = detect_outlier_paths(
        np.array(mean_variance, dtype=np.float32)
    ) if mean_variance else []

    # Pick representative output shape
    first_key = next(iter(outputs), None)
    output_shape = list(outputs[first_key].shape) if first_key else []

    snr_val = float(np.nanmean(all_snr)) if all_snr else 0.0
    if np.isnan(snr_val):
        snr_val = 0.0

    diagnostics = {
        "snr_db": snr_val,
        "variance": mean_variance,
        "null_count": sum(all_null),
        "n_files_processed": len(file_pairs),
        "output_shape": output_shape,
        "outlier_paths": outlier_paths,
        "pca_applied": apply_pca,
        "pca_components": pca_components,
    }

    logger.info("execute_wst complete — %s", json.dumps(diagnostics, indent=2))
    return json.dumps(diagnostics)


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    """Start the MCP server over stdio transport."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    mcp.run()


if __name__ == "__main__":
    main()
