"""
tests/test_foundation.py
========================
Pytest suite validating the TF-C foundation stub (PyTorch module).

Tests:
1. TFCContrastiveLoss returns 0.0 for identical embeddings.
2. TFCContrastiveLoss produces positive loss for different embeddings.
3. MLPProjector output shape matches expected embedding dim.
4. TFCModule end-to-end forward pass produces correct shapes.
"""

from __future__ import annotations

import pytest
import torch

from transient_wst.foundation import (
    MLPProjector,
    TFCContrastiveLoss,
    TFCModule,
)


class TestTFCContrastiveLoss:
    """Tests for the L_TF-C = ||z_T - z_F||² loss."""

    def test_zero_loss_for_identical_embeddings(self) -> None:
        """If z_T == z_F, loss must be exactly 0."""
        loss_fn = TFCContrastiveLoss()
        z = torch.randn(8, 64)
        loss = loss_fn(z, z)
        assert loss.item() == pytest.approx(0.0, abs=1e-7)

    def test_positive_loss_for_different_embeddings(self) -> None:
        """If z_T != z_F, loss must be > 0."""
        loss_fn = TFCContrastiveLoss()
        z_time = torch.randn(8, 64)
        z_freq = torch.randn(8, 64)
        loss = loss_fn(z_time, z_freq)
        assert loss.item() > 0.0

    def test_loss_is_scalar(self) -> None:
        loss_fn = TFCContrastiveLoss()
        loss = loss_fn(torch.randn(4, 32), torch.randn(4, 32))
        assert loss.ndim == 0, "Loss must be a scalar tensor"

    def test_loss_is_differentiable(self) -> None:
        """Loss must support backpropagation."""
        loss_fn = TFCContrastiveLoss()
        z_t = torch.randn(4, 32, requires_grad=True)
        z_f = torch.randn(4, 32, requires_grad=True)
        loss = loss_fn(z_t, z_f)
        loss.backward()
        assert z_t.grad is not None
        assert z_f.grad is not None


class TestMLPProjector:
    """Tests for the 2-layer MLP projector."""

    def test_output_shape_2d(self) -> None:
        """(B, input_dim) → (B, embed_dim)."""
        proj = MLPProjector(input_dim=32, hidden_dim=64, embed_dim=16)
        x = torch.randn(8, 32)
        out = proj(x)
        assert out.shape == (8, 16)

    def test_output_shape_3d(self) -> None:
        """(B, T', input_dim) → (B, T', embed_dim)."""
        proj = MLPProjector(input_dim=32, hidden_dim=64, embed_dim=16)
        x = torch.randn(8, 10, 32)
        out = proj(x)
        assert out.shape == (8, 10, 16)

    def test_different_embed_dims(self) -> None:
        for embed_dim in [8, 32, 128]:
            proj = MLPProjector(input_dim=64, embed_dim=embed_dim)
            out = proj(torch.randn(4, 64))
            assert out.shape[1] == embed_dim


class TestTFCModule:
    """Tests for the end-to-end TF-C alignment stub."""

    def test_forward_returns_three_tensors(self) -> None:
        module = TFCModule(input_dim=32, hidden_dim=64, embed_dim=16)
        x_t = torch.randn(8, 32)
        x_f = torch.randn(8, 32)
        loss, z_t, z_f = module(x_t, x_f)

        assert loss.ndim == 0, "Loss must be scalar"
        assert z_t.shape == (8, 16)
        assert z_f.shape == (8, 16)

    def test_same_input_zero_loss(self) -> None:
        """When time and frequency views are identical, loss should approach 0.
        Note: projectors have different weights, so loss won't be exactly 0
        unless the projectors are identical.
        """
        module = TFCModule(input_dim=16, hidden_dim=32, embed_dim=8)
        # Share weights to test
        module.freq_projector = module.time_projector
        x = torch.randn(4, 16)
        loss, _, _ = module(x, x)
        assert loss.item() == pytest.approx(0.0, abs=1e-6)
