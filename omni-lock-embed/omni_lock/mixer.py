"""
MLP-Mixer Network for Spatial Spreading

Takes a 64-bit watermark and spreads it across the entire image spatially.
Even if 90% of the image is cropped, the remaining 10% contains information
about ALL 64 bits due to the mixing operations.

Architecture:
  W (64 bits) → Linear embed → Token Mixing MLP → Channel Mixing MLP
              → Spatial Projection → Tanh → M_spatial ∈ ℝ^(H×W)
"""

import numpy as np


class MixerNetwork:
    """
    Deterministic MLP-Mixer that maps 64-bit watermark → spatial mask.

    The network weights are derived from a secret key (random seed),
    making the mapping reproducible but unpredictable without the key.

    Parameters
    ----------
    input_dim : int
        Number of watermark bits (default: 64).
    hidden_dim : int
        Hidden layer width (default: 256).
    output_shape : tuple of int
        Spatial dimensions (H, W) of the output mask.
    secret_key : int
        Random seed for deterministic weight initialization.
    """

    def __init__(self, input_dim=64, hidden_dim=256,
                 output_shape=(512, 512), secret_key=42):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_shape = output_shape
        self.secret_key = secret_key

        # Initialize weights deterministically from secret key
        rng = np.random.RandomState(secret_key)

        # Embedding layer: 64 → hidden_dim
        self.embed = rng.randn(input_dim, hidden_dim).astype(np.float32) * 0.1

        # Token mixing MLP: hidden_dim → 2*hidden_dim → hidden_dim
        self.token_mix_w1 = rng.randn(hidden_dim, hidden_dim * 2).astype(np.float32) * 0.1
        self.token_mix_w2 = rng.randn(hidden_dim * 2, hidden_dim).astype(np.float32) * 0.1

        # Channel mixing MLP: hidden_dim → 2*hidden_dim → hidden_dim
        self.channel_mix_w1 = rng.randn(hidden_dim, hidden_dim * 2).astype(np.float32) * 0.1
        self.channel_mix_w2 = rng.randn(hidden_dim * 2, hidden_dim).astype(np.float32) * 0.1

        # Spatial projection: hidden_dim → H*W
        total_pixels = output_shape[0] * output_shape[1]
        self.project = rng.randn(hidden_dim, total_pixels).astype(np.float32) * 0.01

    def forward(self, watermark_bits):
        """
        Map watermark bits to a spatial mask.

        Parameters
        ----------
        watermark_bits : np.ndarray, shape (input_dim,)
            Binary watermark values in {0, 1}.

        Returns
        -------
        mask : np.ndarray, shape (H, W)
            Spatial mask with values in [-1, 1], mean ≈ 0, std ≈ 0.3.
        """
        x = watermark_bits.astype(np.float32)

        # Embed: 64 bits → hidden_dim features
        x = x @ self.embed  # (hidden_dim,)

        # Token mixing: mixes information across bit positions
        residual = x
        x = np.tanh(x @ self.token_mix_w1)  # (2*hidden_dim,)
        x = x @ self.token_mix_w2            # (hidden_dim,)
        x = x + residual                     # Residual connection

        # Channel mixing: mixes across feature channels
        residual = x
        x = np.tanh(x @ self.channel_mix_w1)  # (2*hidden_dim,)
        x = x @ self.channel_mix_w2            # (hidden_dim,)
        x = x + residual                       # Residual connection

        # Project to spatial dimensions
        x = x @ self.project  # (H*W,)
        x = x.reshape(self.output_shape)

        # Normalize to [-1, 1] with controlled magnitude
        x = np.tanh(x)

        return x
