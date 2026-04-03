"""
transient_wst.utils
===================
Shared numerical helpers for SNR computation and anomaly detection.

All functions operate on raw numpy arrays and are intentionally stateless
so they can be composed freely inside both ``core.py`` and ``mcp_server.py``.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def compute_snr_db(
    signal: npt.NDArray[np.float32],
    coefficients: npt.NDArray[np.float32],
) -> float:
    """Estimate the Signal-to-Noise Ratio in decibels.

    Uses the ratio of total scattering-coefficient power to residual
    noise power.  The residual is approximated as the difference between
    the original signal energy and the zeroth-order scattering path
    (the low-pass component).

    Parameters
    ----------
    signal:
        Raw input array of shape ``(B, T)``.
    coefficients:
        Scattering output of shape ``(B, P, T')``.

    Returns
    -------
    float
        SNR in decibels.  Returns ``0.0`` when noise power is negligible
        to avoid division-by-zero.
    """
    signal_power = float(np.mean(signal.astype(np.float64) ** 2))
    coeff_power = float(np.mean(coefficients.astype(np.float64) ** 2))

    noise_power = abs(signal_power - coeff_power)
    if noise_power < 1e-12:
        return 0.0

    snr = 10.0 * np.log10(signal_power / noise_power)
    return float(snr)


def count_anomalous_values(arr: npt.NDArray[np.floating]) -> int:
    """Count NaN and Inf entries in an array.

    Parameters
    ----------
    arr:
        Arbitrary numpy array.

    Returns
    -------
    int
        Total number of non-finite elements.
    """
    return int(np.sum(~np.isfinite(arr)))


def compute_variance_per_path(
    coefficients: npt.NDArray[np.float32],
) -> npt.NDArray[np.float32]:
    """Compute per-scattering-path variance across time and batch.

    Parameters
    ----------
    coefficients:
        Scattering output ``(B, P, T')``.

    Returns
    -------
    ndarray of shape ``(P,)``
        Variance for each scattering path.
    """
    # Collapse batch and time dims → variance along combined axis
    B, P, T_prime = coefficients.shape
    reshaped = coefficients.transpose(1, 0, 2).reshape(P, -1)  # (P, B*T')
    return np.var(reshaped, axis=1).astype(np.float32)


def detect_outlier_paths(
    variance: npt.NDArray[np.float32],
    n_sigma: float = 3.0,
) -> list[int]:
    """Identify scattering paths whose variance exceeds *mean + n_sigma × std*.

    This implements the statistical outlier approach requested for
    domain-agnostic artifact rejection.

    Parameters
    ----------
    variance:
        Per-path variance vector of shape ``(P,)``.
    n_sigma:
        Number of standard deviations above the mean to flag as outlier.

    Returns
    -------
    list[int]
        Indices of outlier scattering paths.
    """
    mean_v = float(np.mean(variance))
    std_v = float(np.std(variance))
    threshold = mean_v + n_sigma * std_v
    return [int(i) for i in np.where(variance > threshold)[0]]
