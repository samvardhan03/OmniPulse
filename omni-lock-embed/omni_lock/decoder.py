"""
WatermarkDecoder — DCT-Domain Decoder

Operates in the same frequency domain as the embedding.
Instead of mapping pixels → bits (hard — must learn to undo DCT),
this decoder maps DCT mid-frequency coefficients → bits (easy — same domain).

Why the previous pixel-space CNN failed:
    The watermark is embedded in DCT mid-frequency coefficients.
    A pixel-space CNN must first learn to compute DCT internally,
    then find the watermark signal, then map to bits.
    With only 4 conv layers and a weak signal, this never converged.

Why DCT-domain works:
    We pre-compute the DCT mid-frequency coefficients (same operation
    as the embedder uses) and feed those directly to an MLP.
    The decoder sees exactly the coefficients that were modified —
    no implicit DCT inversion needed.

Pipeline:
    (B, C, H, W) watermarked image
        ↓  grayscale average
    (B, H, W)
        ↓  batched 8×8 DCT (same D matrix as embedder)
    (B, Hp, Wp) DCT coefficients
        ↓  extract mid-frequency positions (u+v in [2,6])
    (B, N) mid-freq coefficients  [N = num_blocks x num_midfreq_per_block]
        ↓  LayerNorm
    (B, N) normalised
        ↓  Linear(N, 512) + GELU
        ↓  Linear(512, 256) + GELU
        ↓  Linear(256, num_bits) + Sigmoid
    (B, 128) soft decisions

Architecture parameters:
    N at 128x128:  16x16 blocks x 17 mid-freq positions = 4352 coefficients
    MLP:           4352 -> 512 -> 256 -> 128
    Total params:  ~2.4M
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ─────────────────────────────────────────────────────────────────────────────
# DCT helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_dct_matrix(n=8):
    k = torch.arange(n, dtype=torch.float32)
    i = torch.arange(n, dtype=torch.float32)
    D = torch.cos((np.pi / n) * (i.unsqueeze(0) + 0.5) * k.unsqueeze(1))
    D[0]  *= np.sqrt(1.0 / n)
    D[1:] *= np.sqrt(2.0 / n)
    return D

_DCT_MAT = _build_dct_matrix(8)


def _get_D(device):
    return _DCT_MAT.to(device)


def _build_freq_mask():
    mask = torch.zeros(8, 8, dtype=torch.bool)
    for u in range(8):
        for v in range(8):
            if 2 <= (u + v) <= 6:
                mask[u, v] = True
    return mask

_FREQ_MASK = _build_freq_mask()


def _get_freq_mask(device):
    return _FREQ_MASK.to(device)


def _block_dct2d_batched(images, D):
    B, H, W = images.shape
    bh, bw  = H // 8, W // 8
    blocks  = images.view(B, bh, 8, bw, 8)
    blocks  = blocks.permute(0, 1, 3, 2, 4).contiguous()
    blocks  = blocks.view(B * bh * bw, 8, 8)
    n       = B * bh * bw
    D_exp   = D.unsqueeze(0).expand(n, -1, -1)
    Dt_exp  = D.t().unsqueeze(0).expand(n, -1, -1)
    dct_b   = torch.bmm(torch.bmm(D_exp, blocks), Dt_exp)
    dct_b   = dct_b.view(B, bh, bw, 8, 8)
    dct_b   = dct_b.permute(0, 1, 3, 2, 4).contiguous()
    return dct_b.view(B, H, W)


def extract_mid_freq_batch(frames, D, freq_mask):
    """
    Extract mid-frequency DCT coefficients from a batch of frames.

    Parameters
    ----------
    frames    : torch.Tensor, shape (B, C, H, W), float32
    D         : torch.Tensor, shape (8, 8)
    freq_mask : torch.Tensor, shape (8, 8), bool

    Returns
    -------
    coeffs : torch.Tensor, shape (B, N)
    """
    B, C, H, W = frames.shape
    gray = frames.mean(dim=1)                                    # (B, H, W)

    pad_h = (8 - H % 8) % 8
    pad_w = (8 - W % 8) % 8
    if pad_h > 0 or pad_w > 0:
        gray = F.pad(gray.unsqueeze(1),
                     (0, pad_w, 0, pad_h), mode='reflect').squeeze(1)
    Hp, Wp = gray.shape[1], gray.shape[2]

    dct = _block_dct2d_batched(gray, D)                          # (B, Hp, Wp)

    bh, bw    = Hp // 8, Wp // 8
    freq_tile = (freq_mask.float()
                          .unsqueeze(0).unsqueeze(0)
                          .expand(bh, bw, -1, -1)
                          .permute(0, 2, 1, 3)
                          .contiguous()
                          .view(Hp, Wp))
    freq_bool = freq_tile.bool()
    N         = freq_bool.sum().item()
    freq_b    = freq_bool.unsqueeze(0).expand(B, -1, -1)
    coeffs    = dct[freq_b].view(B, N)
    return coeffs                                                # (B, N)


# ─────────────────────────────────────────────────────────────────────────────
# DCT-domain decoder
# ─────────────────────────────────────────────────────────────────────────────

class WatermarkDecoder(nn.Module):
    """
    DCT-domain watermark decoder.

    Extracts mid-frequency DCT coefficients from a watermarked image
    and maps them to soft bit decisions via a small MLP.
    Operates in the same frequency domain as the embedding — no need
    to learn to invert DCT.

    Parameters
    ----------
    num_bits : int   number of watermark bits (128 for LDPC codeword)
    frame_h  : int   expected frame height
    frame_w  : int   expected frame width
    """

    def __init__(self, num_bits=128, frame_h=128, frame_w=128):
        super().__init__()
        self.num_bits = num_bits
        self.frame_h  = frame_h
        self.frame_w  = frame_w

        # Pre-compute N
        Hp    = frame_h + (8 - frame_h % 8) % 8
        Wp    = frame_w + (8 - frame_w % 8) % 8
        bh    = Hp // 8
        bw    = Wp // 8
        n_mid = sum(1 for u in range(8) for v in range(8) if 2 <= u+v <= 6)
        self.N = bh * bw * n_mid
        print(f"[decoder] DCT mid-freq coefficients per frame: {self.N}")

        # MLP operating on DCT coefficients
        self.mlp = nn.Sequential(
            nn.LayerNorm(self.N),
            nn.Linear(self.N, 512),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(512, 256),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_bits),
            nn.Sigmoid()
        )

    def forward(self, x):
        """
        Parameters
        ----------
        x : torch.Tensor, shape (B, C, H, W), float32 in [0, 255]

        Returns
        -------
        soft_decisions : torch.Tensor, shape (B, num_bits), values in (0, 1)
        """
        device    = x.device
        D         = _get_D(device)
        freq_mask = _get_freq_mask(device)
        coeffs    = extract_mid_freq_batch(x, D, freq_mask)  # (B, N)
        return self.mlp(coeffs)                               # (B, num_bits)

    def forward_numpy(self, frame_uint8):
        """
        Inference from a numpy uint8 frame.

        Computes residual = frame - gaussian_blur(frame, sigma=1.5)
        to isolate the mid-frequency watermark signal from image content.
        Same approximation used during training — consistent pipeline.

        Parameters
        ----------
        frame_uint8 : np.ndarray, shape (H, W, 3), dtype uint8

        Returns
        -------
        soft_decisions : np.ndarray, shape (num_bits,)
        confidence     : float in [0, 1]
        """
        self.eval()
        with torch.no_grad():
            t = torch.from_numpy(
                frame_uint8.transpose(2, 0, 1).astype(np.float32)
            ).unsqueeze(0)
            device = next(self.parameters()).device
            t      = t.to(device)

            # Residual: remove smooth image content, keep watermark signal
            smoothed = self._gaussian_blur_tensor(t, sigma=1.5)
            residual = t - smoothed
            soft     = self(residual).squeeze(0).cpu().numpy()

        confidence = float(np.mean(np.abs(soft - 0.5)) * 2.0)
        return soft, confidence

    def _gaussian_blur_tensor(self, x, sigma=1.5):
        """Apply Gaussian blur to (1, C, H, W) tensor — for residual computation."""
        k    = max(3, int(6 * sigma + 1) | 1)
        half = k // 2
        g    = torch.arange(-half, half + 1, dtype=x.dtype, device=x.device)
        k1d  = torch.exp(-g ** 2 / (2 * sigma ** 2))
        k1d  = k1d / k1d.sum()
        C    = x.shape[1]
        kH   = k1d.view(1, 1, -1, 1).expand(C, 1, -1, 1)
        kW   = k1d.view(1, 1, 1, -1).expand(C, 1, 1, -1)
        import torch.nn.functional as F
        x = F.conv2d(x, kH, padding=(half, 0), groups=C)
        x = F.conv2d(x, kW, padding=(0, half), groups=C)
        return x

    def save_weights(self, path):
        torch.save(self.state_dict(), path)
        print(f"[decoder] saved -> {path}")

    def load_weights(self, path, device='cpu'):
        self.load_state_dict(torch.load(path, map_location=device))
        print(f"[decoder] loaded <- {path}")