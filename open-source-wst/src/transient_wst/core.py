"""
transient_wst.core
==================
Primary WaveletScatteringExtractor class and associated dataclasses.

This module wraps Kymatio's ``Scattering1D`` implementation and exposes a
clean, typed interface consumed by the MCP server (mcp_server.py) and
directly by downstream Python clients.

Mathematical foundation
-----------------------
The Wavelet Scattering Transform (WST) constructs a robust signal
representation through an iterative cascade:

*   **S₀x(t)** = x * φ(t)                              — local average
*   **S₁x(t, λ₁)** = |x * ψ_λ₁| * φ(t)                — energy per band
*   **S₂x(t, λ₁, λ₂)** = ||x * ψ_λ₁| * ψ_λ₂| * φ(t)  — transient energy

The representation is translation-invariant and Lipschitz-continuous to
small time-warping deformations, making it ideal for non-stationary
transient detection in any high-noise time-series domain.

Design contract
---------------
* ``WaveletScatteringExtractor`` is intentionally stateless after construction.
  Feed any raw time-series array and receive a ``ScatteringResult``.
* All numpy dtypes are float32 to maintain GPU memory efficiency.
* Raises ``ValueError`` on invalid hyperparameter combinations rather than
  silently producing malformed tensors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import numpy.typing as npt

from transient_wst.utils import (
    compute_snr_db,
    compute_variance_per_path,
    count_anomalous_values,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScatteringResult:
    """Immutable container returned by :meth:`WaveletScatteringExtractor.transform`.

    Attributes
    ----------
    coefficients:
        Raw scattering output tensor of shape ``(B, P, T/2^J)``, where
        ``B`` = batch size, ``P`` = total scattering paths,
        ``T/2^J`` = temporally down-sampled length.
    snr_db:
        Signal-to-Noise Ratio of the output coefficients in decibels.
        Used by the QueryEngine's autonomous evaluation logic.
    null_count:
        Number of NaN or Inf values detected in the output tensor.
    variance:
        Per-path variance vector of shape ``(P,)``.  An abrupt spike in
        any element signals a likely disconnected electrode or artifact.
    meta:
        Arbitrary key/value metadata forwarded from the caller (e.g.,
        subject ID, electrode label).
    """

    coefficients: npt.NDArray[np.float32]
    snr_db: float
    null_count: int
    variance: npt.NDArray[np.float32]
    meta: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core extractor
# ---------------------------------------------------------------------------


class WaveletScatteringExtractor:
    """Cascaded Wavelet Scattering Transform (WST) extractor.

    Wraps ``kymatio.numpy.Scattering1D`` and exposes a minimal, typed API
    designed for integration with the Agentic MCP pipeline.

    Parameters
    ----------
    J : int
        Maximum scale of the scattering transform as a power of two.
        Defines the temporal integration window (``2^J`` samples).
        Valid range: ``1 ≤ J ≤ 16``.
    Q : tuple[int, int]
        ``(Q1, Q2)`` — number of wavelets per octave for the first- and
        second-order filter banks respectively.
        Recommended for EEG: ``Q=(8, 1)`` to ``Q=(16, 2)``.
    T : int | None
        Explicit averaging scale for the low-pass filter.  Defaults to
        ``2^J`` when ``None``.
    sampling_rate : float
        Sampling frequency of the input signal in Hz.  Used for SNR
        computation and diagnostic logging; not passed to Kymatio directly.

    Raises
    ------
    ValueError
        If ``J`` is outside ``[1, 16]`` or either Q component is < 1.

    Examples
    --------
    >>> import numpy as np
    >>> from transient_wst import WaveletScatteringExtractor
    >>> rng = np.random.default_rng(0)
    >>> signal = rng.standard_normal((4, 1024)).astype(np.float32)  # (B, T)
    >>> extractor = WaveletScatteringExtractor(J=6, Q=(8, 1), sampling_rate=256.0)
    >>> result = extractor.transform(signal)
    >>> result.coefficients.shape  # (4, P, T/2^J)
    """

    def __init__(
        self,
        J: int,
        Q: tuple[int, int],
        T: Optional[int] = None,
        sampling_rate: float = 256.0,
    ) -> None:
        self._validate_hyperparameters(J, Q)

        self.J = J
        self.Q = Q
        self.T = T if T is not None else 2**J
        self.sampling_rate = sampling_rate

        # Lazy-initialise Kymatio to avoid import cost at module load time.
        self._scattering = None
        self._n_samples: int | None = None
        logger.info(
            "WaveletScatteringExtractor initialised | J=%d Q=%s T=%d fs=%.1f Hz",
            self.J,
            self.Q,
            self.T,
            self.sampling_rate,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transform(
        self,
        signal: npt.NDArray[np.float32],
        meta: Optional[dict[str, object]] = None,
    ) -> ScatteringResult:
        """Apply the cascaded Wavelet Scattering Transform to *signal*.

        Implements the full S₀, S₁, S₂ cascade:
            S₂x(t, λ₁, λ₂) = ||x * ψ_λ₁| * ψ_λ₂| * φ(t)

        Parameters
        ----------
        signal:
            Input array of shape ``(B, T)`` — batch of 1-D time series.
            Dtype is cast to ``float32`` internally if required.
        meta:
            Optional metadata forwarded verbatim into :class:`ScatteringResult`.

        Returns
        -------
        ScatteringResult
            Structured result including coefficients, SNR, null count, and
            per-path variance — exactly the payload the QueryEngine parses.

        Raises
        ------
        ValueError
            If *signal* is not 2-D or contains fewer samples than ``2^J``.
        RuntimeError
            If the underlying Kymatio execution fails.
        """
        # ── 1. Validate and cast ────────────────────────────────────────
        if signal.ndim != 2:
            raise ValueError(
                f"Signal must be 2-D (B, T); got {signal.ndim}-D with shape {signal.shape}"
            )

        n_samples = signal.shape[1]
        min_samples = 2 ** self.J
        if n_samples < min_samples:
            raise ValueError(
                f"Signal length T={n_samples} is less than 2^J={min_samples}. "
                f"Increase T or decrease J."
            )

        signal = signal.astype(np.float32, copy=False)

        # ── 2. Lazy-init the Kymatio operator ───────────────────────────
        if self._scattering is None or self._n_samples != n_samples:
            self._build_scattering_operator(n_samples)

        # ── 3. Execute Kymatio forward pass ─────────────────────────────
        try:
            coefficients = self._scattering(signal)
        except Exception as exc:
            raise RuntimeError(
                f"Kymatio forward pass failed: {exc}"
            ) from exc

        coefficients = np.asarray(coefficients, dtype=np.float32)

        logger.info(
            "Scattering complete | input=%s → output=%s",
            signal.shape,
            coefficients.shape,
        )

        # ── 4. Compute diagnostics ──────────────────────────────────────
        snr_db = compute_snr_db(signal, coefficients)
        null_count = count_anomalous_values(coefficients)
        variance = compute_variance_per_path(coefficients)

        # ── 5. Return structured result ─────────────────────────────────
        return ScatteringResult(
            coefficients=coefficients,
            snr_db=snr_db,
            null_count=null_count,
            variance=variance,
            meta=meta or {},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_scattering_operator(self, n_samples: int) -> None:
        """Lazily instantiate the Kymatio Scattering1D operator.

        Uses ``kymatio.numpy.Scattering1D`` (CPU backend) for Phase 2.
        GPU acceleration via ``kymatio.torch`` is deferred to Phase 3.

        Parameters
        ----------
        n_samples : int
            Number of time samples ``T`` in the input batch.
        """
        from kymatio.numpy import Scattering1D

        self._scattering = Scattering1D(
            J=self.J,
            shape=(n_samples,),
            Q=self.Q,
            T=self.T,
        )
        self._n_samples = n_samples

        logger.info(
            "Built Scattering1D operator | J=%d Q=%s T=%d shape=(%d,)",
            self.J,
            self.Q,
            self.T,
            n_samples,
        )

    @staticmethod
    def _validate_hyperparameters(J: int, Q: tuple[int, int]) -> None:
        """Raise ``ValueError`` for out-of-range hyperparameters."""
        if not (1 <= J <= 16):
            raise ValueError(f"J must be in [1, 16]; got {J}.")
        if len(Q) != 2:
            raise ValueError(f"Q must be a 2-tuple (Q1, Q2); got {Q!r}.")
        q1, q2 = Q
        if q1 < 1 or q2 < 1:
            raise ValueError(f"Both Q components must be ≥ 1; got Q={Q}.")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"J={self.J}, Q={self.Q}, T={self.T}, "
            f"sampling_rate={self.sampling_rate})"
        )