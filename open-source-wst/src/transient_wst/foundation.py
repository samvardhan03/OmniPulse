"""
transient_wst.foundation
=========================
PyTorch stub for Time-Frequency Consistency (TF-C) contrastive alignment.

Inspired by Meta's TRIBE v2 multi-modal brain encoding and the TF-C
framework (Harvard Zitnik Lab), this module provides:

*   **MLPProjector** — a simple 2-layer MLP that maps PCA-reduced WST
    feature matrices into a compact embedding space suitable for
    tokenization by downstream Transformers.
*   **TFCContrastiveLoss** — implements the alignment loss:
        𝓛_TF-C = ‖z_T − z_F‖²
    ensuring temporal and frequency embeddings converge in a shared
    latent space.
*   **TFCModule** — end-to-end stub that projects time-view and
    frequency-view representations through separate MLPs and computes
    the contrastive loss.

.. note::
    This is a **Phase 2 stub**.  The actual pre-training loop, spectral
    augmentations, and integration with a full Transformer backbone are
    deferred to Phase 3.  The module is fully functional for shape
    validation and loss computation.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class MLPProjector(nn.Module):
    """Two-layer MLP projector for mapping WST features to embedding space.

    Architecture::

        Linear(input_dim → hidden_dim) → ReLU → Linear(hidden_dim → embed_dim)

    Parameters
    ----------
    input_dim : int
        Dimensionality of each input feature vector (number of PCA components K).
    hidden_dim : int
        Width of the hidden layer.
    embed_dim : int
        Dimensionality of the output embedding.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        embed_dim: int = 64,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Project input features to embedding space.

        Parameters
        ----------
        x : Tensor
            Shape ``(B, K)`` or ``(B, T', K)`` — PCA-reduced WST features.
            If 3-D, the projector is applied independently to each time step.

        Returns
        -------
        Tensor
            Shape ``(B, embed_dim)`` or ``(B, T', embed_dim)``.
        """
        return self.net(x)


class TFCContrastiveLoss(nn.Module):
    """Time-Frequency Consistency contrastive loss.

    Computes the squared L2 distance between projected time-domain and
    frequency-domain embeddings:

        𝓛_TF-C = ‖z_T − z_F‖²

    This encourages the model to learn representations where a signal's
    temporal neighbourhood is embedded near its corresponding spectral
    neighbourhood in the shared latent space.
    """

    def forward(
        self,
        z_time: torch.Tensor,
        z_freq: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the TF-C loss.

        Parameters
        ----------
        z_time : Tensor
            Projected time-domain embedding, shape ``(B, embed_dim)``.
        z_freq : Tensor
            Projected frequency-domain embedding, shape ``(B, embed_dim)``.

        Returns
        -------
        Tensor
            Scalar loss value (mean over batch).
        """
        return torch.mean((z_time - z_freq) ** 2)


class TFCModule(nn.Module):
    """End-to-end TF-C alignment module.

    Takes PCA-reduced WST matrices as both the time-view and a
    spectral-view (simple FFT magnitude), projects each through
    separate MLPs, and computes the contrastive loss.

    Parameters
    ----------
    input_dim : int
        Number of PCA components (K) in the reduced WST tensor.
    hidden_dim : int
        Hidden layer width for both projectors.
    embed_dim : int
        Shared embedding dimensionality.

    Examples
    --------
    >>> import torch
    >>> module = TFCModule(input_dim=32, hidden_dim=64, embed_dim=16)
    >>> wst_time = torch.randn(8, 32)   # (B, K)
    >>> wst_freq = torch.randn(8, 32)   # (B, K)
    >>> loss, z_t, z_f = module(wst_time, wst_freq)
    >>> loss.shape
    torch.Size([])
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        embed_dim: int = 64,
    ) -> None:
        super().__init__()
        self.time_projector = MLPProjector(input_dim, hidden_dim, embed_dim)
        self.freq_projector = MLPProjector(input_dim, hidden_dim, embed_dim)
        self.loss_fn = TFCContrastiveLoss()

    def forward(
        self,
        x_time: torch.Tensor,
        x_freq: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Project time and frequency views and compute TF-C loss.

        Parameters
        ----------
        x_time : Tensor
            Time-domain PCA-reduced features, shape ``(B, K)``.
        x_freq : Tensor
            Frequency-domain PCA-reduced features, shape ``(B, K)``.

        Returns
        -------
        tuple[Tensor, Tensor, Tensor]
            ``(loss, z_time, z_freq)`` where loss is a scalar.
        """
        z_time = self.time_projector(x_time)
        z_freq = self.freq_projector(x_freq)
        loss = self.loss_fn(z_time, z_freq)
        return loss, z_time, z_freq
