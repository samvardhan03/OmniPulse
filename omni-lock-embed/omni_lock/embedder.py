"""
DCT Watermark Embedder (Ghost Layer)

Embeds invisible watermark into image frames using dual-domain holography:
1. Spatial spreading via Mixer network → M_spatial
2. Frequency-domain embedding via DCT → mid-frequency coefficients

The watermark hides in DCT mid-frequency coefficients (8 ≤ i+j ≤ 30)
which survive JPEG/H.264 compression while remaining invisible to humans.

Formula:
  Frame_final = IDCT(DCT(Frame_original) + α · DCT(M_spatial))
"""

import numpy as np
import cv2
import torch
import torch.nn as nn
from torch import Tensor
from .mixer import MixerNetwork
from .dct_torch import (
    DifferentiableDCTEmbedder, DCT2D, blockify, deblockify, midfreq_mask
)


def embed_watermark(frame, watermark_64bit, secret_key, alpha=0.1):
    """
    Embed a 64-bit watermark into a single frame using DCT.

    Parameters
    ----------
    frame : np.ndarray, shape (H, W, 3), dtype uint8
        Input RGB frame, pixel values in [0, 255].
    watermark_64bit : np.ndarray, shape (64,)
        Binary watermark values in {0, 1}.
    secret_key : int
        Secret key for Mixer network weight initialization.
    alpha : float
        Embedding strength (0.05–0.2). Higher = more robust but more visible.

    Returns
    -------
    watermarked_frame : np.ndarray, shape (H, W, 3), dtype uint8
        Watermarked frame, visually identical to input.
    spatial_mask : np.ndarray, shape (H, W)
        The spatial mask used for embedding (for visualization/debugging).
    """
    h, w = frame.shape[:2]

    # Pad dimensions to multiples of 8 for DCT block processing
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    h_padded = h + pad_h
    w_padded = w + pad_w

    # Step 1: Generate spatial mask using Mixer
    mixer = MixerNetwork(
        input_dim=len(watermark_64bit),
        hidden_dim=256,
        output_shape=(h_padded, w_padded),
        secret_key=secret_key
    )
    spatial_mask = mixer.forward(watermark_64bit)

    # Scale mask so DCT coefficients are large enough for alpha to matter.
    # Without this, the DCT of tiny 8×8 mask blocks yields sub-pixel
    # changes that vanish after uint8 quantization.
    spatial_mask = spatial_mask * 50.0

    # Step 2: Process each color channel independently
    watermarked = np.pad(
        frame.astype(np.float32),
        ((0, pad_h), (0, pad_w), (0, 0)),
        mode='reflect'
    )

    for ch in range(3):
        channel = watermarked[:, :, ch]

        # Step 3: Process 8×8 blocks
        for i in range(0, h_padded, 8):
            for j in range(0, w_padded, 8):
                block = channel[i:i+8, j:j+8]
                mask_block = spatial_mask[i:i+8, j:j+8].astype(np.float32)

                # Forward DCT
                dct_coeff = cv2.dct(block)
                dct_mask = cv2.dct(mask_block)

                # Embed in mid-frequency band only
                for u in range(8):
                    for v in range(8):
                        freq_sum = u + v
                        if 2 <= freq_sum <= 6:
                            # Mid-frequency band for 8×8 blocks
                            # (i+j range 8-30 is for full image;
                            #  within an 8×8 block, 2-6 is mid-frequency)
                            dct_coeff[u, v] += alpha * dct_mask[u, v]

                # Inverse DCT
                watermarked[i:i+8, j:j+8, ch] = cv2.idct(dct_coeff)

    # Remove padding and clip
    watermarked = watermarked[:h, :w, :]
    watermarked = np.clip(watermarked, 0, 255).astype(np.uint8)

    return watermarked, spatial_mask[:h, :w]


def evaluate_quality(original, watermarked):
    """
    Measure visual quality degradation between original and watermarked frames.

    Parameters
    ----------
    original : np.ndarray, shape (H, W, 3), dtype uint8
    watermarked : np.ndarray, shape (H, W, 3), dtype uint8

    Returns
    -------
    dict with keys:
        'PSNR' : float – Peak Signal-to-Noise Ratio in dB (>35 = imperceptible)
        'SSIM' : float – Structural Similarity Index (>0.95 = excellent)
    """
    from skimage.metrics import structural_similarity

    mse = np.mean((original.astype(np.float64) - watermarked.astype(np.float64)) ** 2)
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 10.0 * np.log10(255.0 ** 2 / mse)

    # SSIM across all channels
    ssim = structural_similarity(
        original, watermarked,
        channel_axis=2,
        data_range=255
    )

    return {'PSNR': psnr, 'SSIM': ssim}


class ResidualEmbedder(nn.Module):
    """
    Residual-domain Wyner-Ziv embedder.

    X_t^wm = X̂_t + (R_t + α · M_t)
    where M_t = T⁻¹(T(M̃_t) ⊗ B) is the mid-freq projection of the
    generator's raw mask M̃_t, and B = {(u,v) : 2 ≤ u+v ≤ 6}.

    M_t = T⁻¹(T(M̃_t) ⊗ B) is a linear operator — no nonlinearity between
    generator output and the residual addition (§4.3 of the plan).
    Clamp is applied only to the final x_wm, not to x_hat/residual/M_t (§4.4).
    """

    def __init__(self, block_size: int = 8, alpha: float = 0.1):
        super().__init__()
        self.block_size = block_size
        self.alpha = alpha
        self.dct = DifferentiableDCTEmbedder(block_size=block_size, alpha=alpha)
        # Register the frequency mask as a buffer so it moves with .to(device)
        self.register_buffer('_freq_mask', midfreq_mask(block_size))

    def project_midfreq(self, mask_raw: Tensor) -> Tensor:
        """
        Apply mid-freq projection: M_t = T⁻¹(T(M̃_t) ⊗ B).

        Parameters
        ----------
        mask_raw : (B, C, H, W) — raw mask M̃_t from generator

        Returns
        -------
        M_t : (B, C, H, W) — mid-frequency projected mask
        """
        B, C, H, W = mask_raw.shape
        device = mask_raw.device

        pad_h = (self.block_size - H % self.block_size) % self.block_size
        pad_w = (self.block_size - W % self.block_size) % self.block_size

        import torch.nn.functional as F
        if pad_h > 0 or pad_w > 0:
            mask_pad = F.pad(mask_raw, (0, pad_w, 0, pad_h), mode='reflect')
        else:
            mask_pad = mask_raw

        shape_pad = mask_pad.shape
        dct_engine = DCT2D(block_size=self.block_size, device=device)

        blocks = blockify(mask_pad, self.block_size)          # (B*C*Nb, bs, bs)
        dct_blocks = dct_engine.dct2(blocks)

        # Apply B mask: multiply by float mask (Hadamard) — no bool indexing (§4.2)
        freq = self._freq_mask.to(device).unsqueeze(0).expand(dct_blocks.size(0), -1, -1)
        dct_filtered = dct_blocks * freq

        idct_blocks = dct_engine.idct2(dct_filtered)
        result_pad = deblockify(idct_blocks, shape_pad, self.block_size)
        return result_pad[:, :, :H, :W]

    def forward(self,
                x_hat: Tensor,
                residual: Tensor,
                mask_raw: Tensor,
                ) -> tuple[Tensor, Tensor]:
        """
        Embed watermark into residual domain.

        Parameters
        ----------
        x_hat    : (B, C, H, W) — X̂_t prediction from simulator
        residual : (B, C, H, W) — R_t = curr_frame − x_hat
        mask_raw : (B, C, H, W) — M̃_t raw mask from generator

        Returns
        -------
        x_wm : (B, C, H, W) — watermarked frame, clamped to [0, 255]
        m_t  : (B, C, H, W) — mid-freq projected mask M_t
        """
        m_t = self.project_midfreq(mask_raw)
        # X_t^wm = X̂_t + R_t + α·M_t  (out-of-place to preserve autograd)
        x_wm = x_hat + residual + self.alpha * m_t
        # Clamp ONLY at the final output — not on x_hat, residual, or m_t (§4.4)
        x_wm = x_wm.clamp(0.0, 255.0)
        return x_wm, m_t
