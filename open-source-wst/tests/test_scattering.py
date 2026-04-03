"""
tests/test_scattering.py
========================
Pytest suite validating the Wavelet Scattering Transform pipeline.

Test strategy:
1.  Generate synthetic time-series with an embedded high-frequency
    transient burst (simulating an EEG spike or FRB).
2.  Run through WaveletScatteringExtractor and verify output tensor
    shape conforms to Kymatio's expected (B, P, T/2^J) format.
3.  Verify SNR is computable and null_count is zero for clean signals.
4.  Verify PCA reducer produces lower-dimensional output.
5.  Verify hyperparameter validation rejects invalid J, Q.
"""

from __future__ import annotations

import numpy as np
import pytest

from transient_wst.core import WaveletScatteringExtractor, ScatteringResult
from transient_wst.reduction import PCAReducer
from transient_wst.utils import (
    compute_snr_db,
    compute_variance_per_path,
    count_anomalous_values,
    detect_outlier_paths,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def synthetic_signal_with_transient() -> np.ndarray:
    """Generate a (B=2, T=1024) signal with an embedded transient burst.

    The signal consists of:
    - Low-frequency baseline (5 Hz sine)
    - High-frequency transient burst (80 Hz) at samples 400–500
    - Gaussian noise (σ=0.3)

    This mimics a non-stationary transient in high-noise data
    (e.g., epileptic spike or FRB).
    """
    rng = np.random.default_rng(42)
    B, T = 2, 1024
    fs = 256.0
    t = np.arange(T) / fs

    signal = np.zeros((B, T), dtype=np.float32)
    for b in range(B):
        # Baseline: 5 Hz sine
        baseline = np.sin(2 * np.pi * 5 * t).astype(np.float32)

        # Transient burst: 80 Hz at samples 400–500
        burst = np.zeros(T, dtype=np.float32)
        burst[400:500] = 3.0 * np.sin(2 * np.pi * 80 * t[400:500]).astype(np.float32)

        # Additive noise
        noise = 0.3 * rng.standard_normal(T).astype(np.float32)

        signal[b] = baseline + burst + noise

    return signal


@pytest.fixture
def extractor() -> WaveletScatteringExtractor:
    """Construct an extractor with parameters suitable for the 1024-sample signal."""
    return WaveletScatteringExtractor(J=6, Q=(8, 1), sampling_rate=256.0)


# ── Core transform tests ─────────────────────────────────────────────────────


class TestWaveletScatteringExtractor:
    """Tests for WaveletScatteringExtractor.transform()."""

    def test_output_shape_matches_kymatio_spec(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """Output shape must be (B, P, T/2^J)."""
        signal = synthetic_signal_with_transient
        result = extractor.transform(signal)

        B, T = signal.shape
        expected_time_dim = T // (2 ** extractor.J)  # T / 2^J

        assert result.coefficients.ndim == 3, (
            f"Expected 3D tensor, got {result.coefficients.ndim}D"
        )
        assert result.coefficients.shape[0] == B, (
            f"Batch dim mismatch: {result.coefficients.shape[0]} != {B}"
        )
        assert result.coefficients.shape[2] == expected_time_dim, (
            f"Time dim: {result.coefficients.shape[2]} != {expected_time_dim}"
        )
        # P (paths) should be > 0
        assert result.coefficients.shape[1] > 0, "No scattering paths produced"

    def test_result_is_scattering_result(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """Return type must be ScatteringResult dataclass."""
        result = extractor.transform(synthetic_signal_with_transient)
        assert isinstance(result, ScatteringResult)

    def test_coefficients_are_float32(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """Coefficients must be float32 for GPU memory efficiency."""
        result = extractor.transform(synthetic_signal_with_transient)
        assert result.coefficients.dtype == np.float32

    def test_no_null_values_in_clean_signal(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """A clean synthetic signal should produce zero NaN/Inf values."""
        result = extractor.transform(synthetic_signal_with_transient)
        assert result.null_count == 0, f"Found {result.null_count} NaN/Inf values"

    def test_snr_is_computed(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """SNR should be a finite (non-NaN) number."""
        result = extractor.transform(synthetic_signal_with_transient)
        assert np.isfinite(result.snr_db), f"SNR is not finite: {result.snr_db}"

    def test_variance_shape_matches_paths(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """Per-path variance vector shape must be (P,)."""
        result = extractor.transform(synthetic_signal_with_transient)
        P = result.coefficients.shape[1]
        assert result.variance.shape == (P,), (
            f"Variance shape {result.variance.shape} != ({P},)"
        )

    def test_meta_forwarded(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """Metadata passed to transform() must appear in the result."""
        meta = {"subject": "S01", "channel": "Fz"}
        result = extractor.transform(synthetic_signal_with_transient, meta=meta)
        assert result.meta == meta


# ── Hyperparameter validation ─────────────────────────────────────────────────


class TestHyperparameterValidation:
    """Verify that invalid hyperparameters are rejected at construction."""

    def test_j_too_small(self) -> None:
        with pytest.raises(ValueError, match="J must be in"):
            WaveletScatteringExtractor(J=0, Q=(8, 1))

    def test_j_too_large(self) -> None:
        with pytest.raises(ValueError, match="J must be in"):
            WaveletScatteringExtractor(J=17, Q=(8, 1))

    def test_q_component_zero(self) -> None:
        with pytest.raises(ValueError, match="Q components must be"):
            WaveletScatteringExtractor(J=6, Q=(0, 1))

    def test_q_wrong_length(self) -> None:
        with pytest.raises(ValueError, match="2-tuple"):
            WaveletScatteringExtractor(J=6, Q=(8,))  # type: ignore[arg-type]

    def test_signal_too_short(self, extractor: WaveletScatteringExtractor) -> None:
        """Signal shorter than 2^J must raise ValueError."""
        short_signal = np.zeros((1, 32), dtype=np.float32)  # 32 < 2^6=64
        with pytest.raises(ValueError, match="less than"):
            extractor.transform(short_signal)

    def test_signal_wrong_ndim(self, extractor: WaveletScatteringExtractor) -> None:
        """1-D signal must raise ValueError (requires 2-D batch)."""
        with pytest.raises(ValueError, match="2-D"):
            extractor.transform(np.zeros(1024, dtype=np.float32))


# ── PCA reduction ─────────────────────────────────────────────────────────────


class TestPCAReducer:
    """Tests for PCAReducer dimensionality reduction."""

    def test_reduces_path_dimension(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """PCA should reduce P (scattering paths) to K < P."""
        result = extractor.transform(synthetic_signal_with_transient)
        reducer = PCAReducer(variance_threshold=0.95)
        reduced = reducer.fit_transform(result.coefficients)

        _, P_original, T_prime = result.coefficients.shape
        _, K_reduced, T_prime_r = reduced.shape

        assert K_reduced < P_original, (
            f"PCA did not reduce dimensions: K={K_reduced} >= P={P_original}"
        )
        assert T_prime_r == T_prime, "Time dimension should not change"

    def test_output_is_float32(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        result = extractor.transform(synthetic_signal_with_transient)
        reducer = PCAReducer(variance_threshold=0.95)
        reduced = reducer.fit_transform(result.coefficients)
        assert reduced.dtype == np.float32

    def test_transform_after_fit(
        self,
        extractor: WaveletScatteringExtractor,
        synthetic_signal_with_transient: np.ndarray,
    ) -> None:
        """transform() should work after fit_transform() without error."""
        result = extractor.transform(synthetic_signal_with_transient)
        reducer = PCAReducer(variance_threshold=0.95)
        _ = reducer.fit_transform(result.coefficients)

        # Apply to same data — should succeed
        out = reducer.transform(result.coefficients)
        assert out.shape[1] == reducer.n_components

    def test_not_fitted_raises(self) -> None:
        reducer = PCAReducer()
        with pytest.raises(RuntimeError, match="not been fitted"):
            reducer.transform(np.zeros((2, 10, 5), dtype=np.float32))


# ── Utility functions ─────────────────────────────────────────────────────────


class TestUtils:
    def test_compute_snr_db(self) -> None:
        signal = np.ones((1, 100), dtype=np.float32)
        coeffs = np.ones((1, 10, 10), dtype=np.float32) * 0.9
        snr = compute_snr_db(signal, coeffs)
        assert np.isfinite(snr)

    def test_count_anomalous_clean(self) -> None:
        arr = np.ones((3, 4), dtype=np.float32)
        assert count_anomalous_values(arr) == 0

    def test_count_anomalous_with_nan(self) -> None:
        arr = np.array([1.0, np.nan, np.inf, -np.inf, 2.0], dtype=np.float32)
        assert count_anomalous_values(arr) == 3

    def test_variance_per_path(self) -> None:
        # (B=2, P=3, T'=4) — constant values → variance = 0
        coeffs = np.ones((2, 3, 4), dtype=np.float32)
        var = compute_variance_per_path(coeffs)
        assert var.shape == (3,)
        np.testing.assert_allclose(var, 0.0, atol=1e-7)

    def test_detect_outlier_paths(self) -> None:
        # Use a very extreme outlier (1000x) that survives mean-pollution
        variance = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 10000.0], dtype=np.float32)
        outliers = detect_outlier_paths(variance, n_sigma=2.0)
        assert 5 in outliers
