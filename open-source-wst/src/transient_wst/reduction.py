"""
transient_wst.reduction
=======================
Dimensionality reduction of Wavelet Scattering coefficient tensors via
Principal Component Analysis (PCA).

After the WST produces a ``(B, P, T')`` tensor with potentially hundreds
of scattering paths ``P``, PCA projects the path dimension into a compact
``K``-dimensional latent space retaining ≥ 95 % of the variance.  The
resulting ``(B, K, T')`` tensor is optimal for downstream Transformer
tokenization (TFM-Tokenizer / TF-C alignment).
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import numpy.typing as npt
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class PCAReducer:
    """PCA-based dimensionality reduction along the scattering-path axis.

    Parameters
    ----------
    variance_threshold : float
        Minimum cumulative explained variance ratio to retain.
        Defaults to ``0.95`` (95 %).
    n_components : int | None
        If given, overrides *variance_threshold* and keeps exactly
        this many components.

    Examples
    --------
    >>> import numpy as np
    >>> from transient_wst.reduction import PCAReducer
    >>> coeffs = np.random.randn(4, 120, 16).astype(np.float32)
    >>> reducer = PCAReducer(variance_threshold=0.95)
    >>> reduced = reducer.fit_transform(coeffs)
    >>> reduced.shape[1] < 120   # K < P
    True
    """

    def __init__(
        self,
        variance_threshold: float = 0.95,
        n_components: Optional[int] = None,
    ) -> None:
        if n_components is not None:
            self._pca = PCA(n_components=n_components)
        else:
            self._pca = PCA(n_components=variance_threshold, svd_solver="full")

        self.variance_threshold = variance_threshold
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit_transform(
        self,
        coefficients: npt.NDArray[np.float32],
    ) -> npt.NDArray[np.float32]:
        """Fit PCA on *coefficients* and return the reduced tensor.

        The input ``(B, P, T')`` tensor is reshaped to ``(B * T', P)``
        for PCA fitting (treating each time-step of every batch element
        as an independent observation in the ``P``-dimensional scattering
        feature space).  After projection, the result is reshaped back
        to ``(B, K, T')``.

        Parameters
        ----------
        coefficients:
            Scattering output tensor of shape ``(B, P, T')``.

        Returns
        -------
        ndarray of shape ``(B, K, T')``
            PCA-reduced tensor where ``K ≤ P``.
        """
        B, P, T_prime = coefficients.shape

        # Reshape: each (path vector at a given time-step) is one sample
        flat = coefficients.transpose(0, 2, 1).reshape(B * T_prime, P)

        reduced_flat = self._pca.fit_transform(flat).astype(np.float32)
        self._is_fitted = True

        K = reduced_flat.shape[1]
        reduced = reduced_flat.reshape(B, T_prime, K).transpose(0, 2, 1)

        logger.info(
            "PCA fit_transform | P=%d → K=%d  (%.1f%% variance retained, %d components)",
            P,
            K,
            sum(self._pca.explained_variance_ratio_) * 100,
            K,
        )

        return reduced

    def transform(
        self,
        coefficients: npt.NDArray[np.float32],
    ) -> npt.NDArray[np.float32]:
        """Apply a previously fitted PCA projection.

        Parameters
        ----------
        coefficients:
            Scattering output tensor ``(B, P, T')``.

        Returns
        -------
        ndarray of shape ``(B, K, T')``
        """
        if not self._is_fitted:
            raise RuntimeError("PCAReducer has not been fitted yet. Call fit_transform first.")

        B, P, T_prime = coefficients.shape
        flat = coefficients.transpose(0, 2, 1).reshape(B * T_prime, P)

        reduced_flat = self._pca.transform(flat).astype(np.float32)
        K = reduced_flat.shape[1]
        return reduced_flat.reshape(B, T_prime, K).transpose(0, 2, 1)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def n_components(self) -> int:
        """Number of retained principal components after fitting."""
        if not self._is_fitted:
            raise RuntimeError("PCAReducer has not been fitted yet.")
        return int(self._pca.n_components_)

    @property
    def explained_variance_ratio(self) -> npt.NDArray[np.float64]:
        """Per-component explained variance ratio."""
        if not self._is_fitted:
            raise RuntimeError("PCAReducer has not been fitted yet.")
        return self._pca.explained_variance_ratio_

    def __repr__(self) -> str:
        status = f"fitted={self._is_fitted}"
        if self._is_fitted:
            status += f", K={self.n_components}"
        return f"PCAReducer(threshold={self.variance_threshold}, {status})"
