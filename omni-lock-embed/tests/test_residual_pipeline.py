"""
P3C-7 — Mandatory residual-pipeline tests.

Run with: pytest tests/test_residual_pipeline.py -v
Phase 4 cannot start until all tests here are green.
"""

import math
import torch
import torch.nn as nn
import pytest

from omni_lock.flow import SpyNetLite, bilinear_warp
from omni_lock.temporal_video import DifferentiableHEVCSimulator
from omni_lock.embedder import ResidualEmbedder
from omni_lock.losses import soft_parity_loss
from omni_lock.mixer_torch import MixerTorch


# ─────────────────────────────────────────────────────────────────────────────
# 5.1 Shape contracts
# ─────────────────────────────────────────────────────────────────────────────

def test_simulator_shapes():
    sim = DifferentiableHEVCSimulator(SpyNetLite())
    prev = torch.rand(2, 3, 64, 64) * 255
    curr = torch.rand(2, 3, 64, 64) * 255
    x_hat, residual, flow = sim(prev, curr)
    assert x_hat.shape == (2, 3, 64, 64)
    assert residual.shape == (2, 3, 64, 64)
    assert flow.shape == (2, 2, 64, 64)


def test_residual_embedder_shapes():
    emb = ResidualEmbedder()
    x_hat = torch.rand(1, 3, 64, 64) * 200
    residual = torch.rand(1, 3, 64, 64) * 20
    mask = torch.randn(1, 3, 64, 64)
    x_wm, m_t = emb(x_hat, residual, mask)
    assert x_wm.shape == (1, 3, 64, 64)
    assert m_t.shape == (1, 3, 64, 64)


# ─────────────────────────────────────────────────────────────────────────────
# 5.2 Headline test — gradient flow: residual → motion vectors
# ─────────────────────────────────────────────────────────────────────────────

def test_gradient_flows_to_flow():
    sim = DifferentiableHEVCSimulator(SpyNetLite())
    prev = torch.rand(1, 3, 32, 32) * 255
    curr = torch.rand(1, 3, 32, 32) * 255
    x_hat, residual, flow = sim(prev, curr)
    residual.pow(2).mean().backward()
    flow_params = list(sim.flow_estimator.parameters())
    assert all(p.grad is not None for p in flow_params)
    assert any(p.grad.abs().sum() > 0 for p in flow_params)


# ─────────────────────────────────────────────────────────────────────────────
# 5.3 End-to-end grad: parity loss → mixer through residual embedder
# ─────────────────────────────────────────────────────────────────────────────

def test_end_to_end_grad_through_embedder():
    """
    mixer → mask_raw → ResidualEmbedder → WatermarkDecoder → soft_parity_loss.
    Asserts mixer.embed.weight.grad has non-zero L1 after one backward.
    """
    from omni_lock.decoder import WatermarkDecoder

    H_FRAME, W_FRAME = 32, 32
    NUM_BITS = 64

    mixer = MixerTorch(key_size=NUM_BITS, embed_dim=64, spatial_dim=3 * H_FRAME * W_FRAME)
    decoder = WatermarkDecoder(num_bits=NUM_BITS, frame_h=H_FRAME, frame_w=W_FRAME)
    emb = ResidualEmbedder(alpha=0.1)

    # Synthetic parity-check matrix (no pyldpc needed)
    torch.manual_seed(0)
    H_check = torch.randint(0, 2, (32, NUM_BITS)).float()

    bits = torch.rand(1, NUM_BITS)
    mask_flat = mixer(bits)                                    # (1, 3*H*W)
    mask_raw = mask_flat.view(1, 3, H_FRAME, W_FRAME)

    # Dummy x_hat and residual (no gradient needed from simulator for this test)
    x_hat = torch.rand(1, 3, H_FRAME, W_FRAME).detach() * 200
    residual = torch.rand(1, 3, H_FRAME, W_FRAME).detach() * 20

    x_wm, _ = emb(x_hat, residual, mask_raw)

    soft_bits = decoder(x_wm)                                 # (1, NUM_BITS)
    loss = soft_parity_loss(soft_bits, H_check)
    loss.backward()

    assert mixer.embed.weight.grad is not None
    assert mixer.embed.weight.grad.abs().sum() > 0


# ─────────────────────────────────────────────────────────────────────────────
# 5.4 Mid-freq projection idempotent
# ─────────────────────────────────────────────────────────────────────────────

def test_midfreq_projection_idempotent():
    emb = ResidualEmbedder()
    m = torch.randn(1, 3, 64, 64)
    proj_once = emb.project_midfreq(m)
    proj_twice = emb.project_midfreq(proj_once)
    assert torch.allclose(proj_twice, proj_once, atol=1e-4)


# ─────────────────────────────────────────────────────────────────────────────
# 5.5 PSNR transparency  (α=0.1, must exceed 35 dB)
# ─────────────────────────────────────────────────────────────────────────────

def _psnr(a: torch.Tensor, b: torch.Tensor) -> float:
    mse = (a.float() - b.float()).pow(2).mean().item()
    if mse < 1e-10:
        return float('inf')
    return 10.0 * math.log10(255.0 ** 2 / mse)


def test_psnr_above_35db():
    torch.manual_seed(7)
    # Natural-image-spectrum input: smoothed random tensor
    raw = torch.rand(1, 3, 64, 64) * 255
    # Smooth with average pool to mimic natural-image low-frequency content
    smooth = nn.functional.avg_pool2d(
        nn.functional.avg_pool2d(raw, 3, stride=1, padding=1),
        3, stride=1, padding=1
    )

    emb = ResidualEmbedder(alpha=0.1)

    # Simulate a minimal path: zero x_hat, full smooth as 'frame'
    x_hat = torch.zeros_like(smooth)
    residual = smooth - x_hat          # residual = smooth (trivial I-frame)
    mask_raw = torch.randn_like(smooth) * 0.1

    x_wm, _ = emb(x_hat, residual, mask_raw)

    psnr = _psnr(smooth, x_wm)
    assert psnr > 35.0, f"PSNR {psnr:.2f} dB < 35 dB — transparency regression"


# ─────────────────────────────────────────────────────────────────────────────
# 5.6 grid_sample flag regression — 0.5 px translation round-trip
# ─────────────────────────────────────────────────────────────────────────────

def test_grid_sample_roundtrip_residual():
    """
    Shift image right by 0.5 px then left by 0.5 px.
    Round-trip residual energy relative to original must be below 5%.
    Validates correct mode/padding/align_corners flags in bilinear_warp.
    """
    torch.manual_seed(3)
    # Use a smooth image so bilinear interp errors are small
    img = nn.functional.avg_pool2d(
        torch.rand(1, 3, 64, 64) * 255,
        5, stride=1, padding=2
    )
    flow_right = torch.zeros(1, 2, 64, 64)
    flow_right[:, 0] = 0.5

    flow_left = torch.zeros(1, 2, 64, 64)
    flow_left[:, 0] = -0.5

    warped_right = bilinear_warp(img, flow_right)
    warped_back = bilinear_warp(warped_right, flow_left)

    residual_energy = (warped_back - img).pow(2).mean()
    original_energy = img.pow(2).mean()
    ratio = (residual_energy / original_energy).item()
    assert ratio < 0.05, f"Round-trip residual ratio {ratio:.4f} ≥ 0.05 — grid_sample flags may be wrong"


# ─────────────────────────────────────────────────────────────────────────────
# 5.7 No NaN/Inf — 50 forward+backward iterations
# ─────────────────────────────────────────────────────────────────────────────

def test_no_nan_inf_50_iterations():
    """
    50 forward+backward passes on random inputs.
    torch.isfinite must hold on every parameter gradient.
    """
    torch.manual_seed(99)
    sim = DifferentiableHEVCSimulator(SpyNetLite())
    emb = ResidualEmbedder()

    all_params = list(sim.parameters()) + list(emb.parameters())

    for _ in range(50):
        prev = torch.rand(1, 3, 32, 32) * 255
        curr = torch.rand(1, 3, 32, 32) * 255
        mask = torch.randn(1, 3, 32, 32)

        x_hat, residual, flow = sim(prev, curr)
        x_wm, _ = emb(x_hat, residual, mask)

        loss = x_wm.pow(2).mean() + flow.pow(2).mean()
        loss.backward()

    for p in all_params:
        if p.grad is not None:
            assert torch.isfinite(p.grad).all(), \
                f"Non-finite gradient in parameter of shape {p.shape}"
