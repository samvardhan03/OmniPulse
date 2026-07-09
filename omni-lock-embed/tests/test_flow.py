"""
P3C-1 tests — SpyNetLite optical flow module.
Run with: pytest tests/test_flow.py -v
"""

import torch
import pytest
from omni_lock.flow import SpyNetLite, bilinear_warp


class TestBilinearWarp:
    def test_zero_flow_is_identity(self):
        img = torch.rand(1, 3, 32, 32) * 255
        flow = torch.zeros(1, 2, 32, 32)
        warped = bilinear_warp(img, flow)
        assert warped.shape == img.shape
        # grid_sample with bilinear interpolation has ~1e-3 float32 round-trip error
        assert torch.allclose(warped, img, atol=1e-2)

    def test_output_shape(self):
        img = torch.rand(2, 3, 64, 64)
        flow = torch.rand(2, 2, 64, 64)
        out = bilinear_warp(img, flow)
        assert out.shape == (2, 3, 64, 64)

    def test_gradient_flows_through_warp(self):
        img = torch.rand(1, 3, 32, 32, requires_grad=True)
        flow = torch.rand(1, 2, 32, 32, requires_grad=True)
        warped = bilinear_warp(img, flow)
        warped.sum().backward()
        assert img.grad is not None
        assert flow.grad is not None

    def test_large_shift_bounded(self):
        """Warp output stays in a bounded range even with large flow values."""
        torch.manual_seed(0)
        img = torch.rand(1, 3, 32, 32) * 255
        flow = torch.ones(1, 2, 32, 32) * 1000.0  # very large shift
        warped = bilinear_warp(img, flow)
        # With padding_mode='border', all out-of-bounds pixels clamp to border
        assert torch.isfinite(warped).all()
        assert warped.min() >= 0.0
        assert warped.max() <= 255.0 + 1e-3


class TestSpyNetLite:
    def test_forward_shape(self):
        model = SpyNetLite()
        prev = torch.rand(2, 3, 64, 64) * 255
        curr = torch.rand(2, 3, 64, 64) * 255
        flow = model(prev, curr)
        assert flow.shape == (2, 2, 64, 64)

    def test_output_dtype(self):
        model = SpyNetLite()
        prev = torch.rand(1, 3, 32, 32) * 255
        curr = torch.rand(1, 3, 32, 32) * 255
        flow = model(prev, curr)
        assert flow.dtype == torch.float32

    def test_gradient_flows(self):
        model = SpyNetLite()
        prev = torch.rand(1, 3, 32, 32) * 255
        curr = torch.rand(1, 3, 32, 32) * 255
        flow = model(prev, curr)
        flow.pow(2).mean().backward()
        params = list(model.parameters())
        assert all(p.grad is not None for p in params)
        assert any(p.grad.abs().sum() > 0 for p in params)

    def test_no_nan_in_output(self):
        torch.manual_seed(0)
        model = SpyNetLite()
        prev = torch.rand(2, 3, 64, 64) * 255
        curr = torch.rand(2, 3, 64, 64) * 255
        flow = model(prev, curr)
        assert torch.isfinite(flow).all()

    def test_batch_size_one(self):
        model = SpyNetLite()
        prev = torch.rand(1, 3, 32, 32) * 255
        curr = torch.rand(1, 3, 32, 32) * 255
        flow = model(prev, curr)
        assert flow.shape == (1, 2, 32, 32)

    def test_custom_levels(self):
        model = SpyNetLite(num_levels=2, base_channels=8)
        prev = torch.rand(1, 3, 32, 32) * 255
        curr = torch.rand(1, 3, 32, 32) * 255
        flow = model(prev, curr)
        assert flow.shape == (1, 2, 32, 32)
