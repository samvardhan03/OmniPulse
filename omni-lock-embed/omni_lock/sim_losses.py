"""
Simulator losses for DifferentiableHEVCSimulator (Phase 3C).

L_sim = λ1·L_spatial + λ2·L_spectral + λ3·L_rate

Surrogate R_true approximation (no real HEVC encoder in Phase 3C):
    R_true ≈ X_t − bilinear_warp(X_{t-1}, optical_flow_target)
where optical_flow_target comes from a frozen-weights copy of SpyNetLite
initialised from the same seed.  This is a known approximation; it will be
replaced by ffmpeg-extracted HEVC residuals in a future phase
(Roadmap §4.3 Step 4).

Gaussian-mixture entropy estimator: K=4 components, used in L_rate.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .dct_torch import DCT2D, blockify, deblockify, midfreq_mask
from .ste import StraightThroughEstimator


# ─────────────────────────────────────────────────────────────────────────────
# SSIM helper (differentiable, window-based)
# ─────────────────────────────────────────────────────────────────────────────

def _gaussian_kernel_1d(window_size: int, sigma: float, device, dtype) -> Tensor:
    half = window_size // 2
    g = torch.arange(-half, half + 1, device=device, dtype=dtype)
    k = torch.exp(-g ** 2 / (2 * sigma ** 2))
    return k / k.sum()


def _ssim(x: Tensor, y: Tensor, window_size: int = 11, sigma: float = 1.5) -> Tensor:
    """Differentiable SSIM in [-1, 1] range; returns scalar mean."""
    C = x.shape[1]
    k1d = _gaussian_kernel_1d(window_size, sigma, x.device, x.dtype)
    k2d = k1d.unsqueeze(1) @ k1d.unsqueeze(0)
    kernel = k2d.expand(C, 1, window_size, window_size)

    pad = window_size // 2
    mu_x = F.conv2d(x, kernel, padding=pad, groups=C)
    mu_y = F.conv2d(y, kernel, padding=pad, groups=C)

    mu_x2, mu_y2, mu_xy = mu_x ** 2, mu_y ** 2, mu_x * mu_y
    sig_x = F.conv2d(x * x, kernel, padding=pad, groups=C) - mu_x2
    sig_y = F.conv2d(y * y, kernel, padding=pad, groups=C) - mu_y2
    sig_xy = F.conv2d(x * y, kernel, padding=pad, groups=C) - mu_xy

    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    num = (2 * mu_xy + C1) * (2 * sig_xy + C2)
    den = (mu_x2 + mu_y2 + C1) * (sig_x + sig_y + C2)
    return (num / den).mean()


# ─────────────────────────────────────────────────────────────────────────────
# Gaussian-mixture entropy estimator  (K=4 components)
# ─────────────────────────────────────────────────────────────────────────────

class GaussianMixtureEntropy(nn.Module):
    """
    Differentiable entropy estimator via K=4 Gaussian mixture model.

    H(Q(x)) ≈ -E[log p_GMM(x)]  where p_GMM is a learned mixture density.
    Parameters (means, log-scales, log-weights) are NOT registered as model
    parameters here — the estimator is re-initialised each forward call from
    the data statistics for a self-supervised proxy.
    """

    def __init__(self, num_components: int = 4):
        super().__init__()
        self.K = num_components

    def forward(self, x: Tensor) -> Tensor:
        """
        Parameters
        ----------
        x : (B, C, H, W) float32

        Returns
        -------
        entropy_proxy : scalar tensor, gradient-attached
        """
        flat = x.reshape(-1)
        N = flat.shape[0]

        # Initialise GMM parameters from data statistics (no external optimiser needed)
        std_data = flat.std().detach().clamp(min=1e-3)
        means = torch.linspace(-std_data, std_data, self.K, device=x.device, dtype=x.dtype)
        log_scales = torch.zeros(self.K, device=x.device, dtype=x.dtype)
        log_weights = torch.zeros(self.K, device=x.device, dtype=x.dtype)

        scales = log_scales.exp().clamp(min=1e-3)
        weights = F.softmax(log_weights, dim=0)  # (K,)

        # Log-likelihood: log sum_k w_k * N(x; mu_k, sigma_k)
        x_exp = flat.unsqueeze(1)        # (N, 1)
        mu = means.unsqueeze(0)          # (1, K)
        sig = scales.unsqueeze(0)        # (1, K)

        log_gauss = (
            -0.5 * ((x_exp - mu) / sig) ** 2
            - sig.log()
            - 0.5 * math.log(2 * math.pi)
        )                                # (N, K)
        log_mix = torch.logsumexp(log_gauss + weights.log().unsqueeze(0), dim=1)  # (N,)
        return -log_mix.mean()


# ─────────────────────────────────────────────────────────────────────────────
# Spectral helper: mid-freq DCT residual
# ─────────────────────────────────────────────────────────────────────────────

def _spectral_residual(R_true: Tensor, R_sim: Tensor, block_size: int = 8) -> Tensor:
    """|| B ⊗ (T(R_true) − T(R_sim)) ||_2^2  (mean over blocks)."""
    device = R_true.device
    B, C, H, W = R_true.shape

    pad_h = (block_size - H % block_size) % block_size
    pad_w = (block_size - W % block_size) % block_size
    if pad_h > 0 or pad_w > 0:
        R_true = F.pad(R_true, (0, pad_w, 0, pad_h), mode='reflect')
        R_sim = F.pad(R_sim, (0, pad_w, 0, pad_h), mode='reflect')

    shape_pad = R_true.shape
    dct_engine = DCT2D(block_size=block_size, device=device)

    def _dct_blocks(t):
        blk = blockify(t, block_size)
        return dct_engine.dct2(blk)

    freq_b = midfreq_mask(block_size).to(device)

    dct_true = _dct_blocks(R_true)   # (B*C*Nb, bs, bs)
    dct_sim = _dct_blocks(R_sim)

    diff = (dct_true - dct_sim) * freq_b.unsqueeze(0).expand(dct_true.size(0), -1, -1)
    return diff.pow(2).mean()


# ─────────────────────────────────────────────────────────────────────────────
# Main loss
# ─────────────────────────────────────────────────────────────────────────────

_ste = StraightThroughEstimator()
_gme = GaussianMixtureEntropy(num_components=4)


def simulator_loss(
    R_true: Tensor,
    R_sim: Tensor,
    lambdas: tuple[float, float, float] = (1.0, 0.5, 0.1),
    beta: float = 0.2,
    lambda_qp: float = 0.1,
) -> Tensor:
    """
    Composite simulator loss:

        L_sim = λ1·L_spatial + λ2·L_spectral + λ3·L_rate

    where
        L_spatial  = ||R_true − R_sim||_1 + β·(1 − MS-SSIM(R_true, R_sim))
        L_spectral = || B ⊗ (T(R_true) − T(R_sim)) ||_2^2
        L_rate     = | (D(R_true) + λ_QP·R_bits(R_true))
                      − (D(R_sim)  + λ_QP·H(Q(R_sim))) |_1

    Surrogate R_true: see module docstring.

    Parameters
    ----------
    R_true     : (B, C, H, W) surrogate true residual
    R_sim      : (B, C, H, W) simulated residual
    lambdas    : (λ1, λ2, λ3) loss weighting
    beta       : weight of (1-SSIM) within L_spatial
    lambda_qp  : QP-analogous rate-distortion tradeoff weight
    """
    lambda1, lambda2, lambda3 = lambdas

    # L_spatial: L1 + β·(1 − SSIM)
    l_spatial = (R_true - R_sim).abs().mean() + beta * (1.0 - _ssim(R_true, R_sim))

    # L_spectral: mid-freq DCT difference
    l_spectral = _spectral_residual(R_true, R_sim)

    # L_rate: distortion + entropy proxy
    # D(·) = mean squared value (proxy for distortion)
    d_true = R_true.pow(2).mean()
    d_sim = R_sim.pow(2).mean()

    # R_bits proxy: entropy estimator on STE-quantised R_sim
    r_sim_q = _ste(R_sim / 255.0) * 255.0  # STE round-trip (§4.2 forbidden ops rule)
    h_q_sim = _gme(r_sim_q)

    # R_bits(R_true): entropy of R_true (no quantisation needed for surrogate)
    r_bits_true = _gme(R_true)

    l_rate = (
        (d_true + lambda_qp * r_bits_true)
        - (d_sim + lambda_qp * h_q_sim)
    ).abs()

    return lambda1 * l_spatial + lambda2 * l_spectral + lambda3 * l_rate
