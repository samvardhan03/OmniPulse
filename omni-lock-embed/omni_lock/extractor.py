"""
Watermark Extractor — CNN Decoder Version

Replaces the correlation-based extractor with a trained CNN decoder.

The old approach (correlation) failed because:
  - Required Mixer to embed 128 orthogonal patterns in one mask
  - At 128×128 resolution this caused bit collapse
  - Many bits produced identical correlation values

The new approach (CNN decoder):
  - A small CNN maps the watermarked image directly to soft bit decisions
  - No correlation, no reference masks, no secret key needed at extraction
  - Decoder and Mixer are trained end-to-end together
  - Decoder learns whatever extraction strategy works best

Usage
-----
    from extractor import extract_watermark, load_decoder

    # Load trained decoder
    decoder = load_decoder('checkpoints/decoder.pt')

    # Extract from a frame
    soft_bits, confidence = extract_watermark(frame, decoder)
"""

import numpy as np
import torch

from .decoder import WatermarkDecoder


# ─────────────────────────────────────────────────────────────────────────────
# Load decoder
# ─────────────────────────────────────────────────────────────────────────────

def load_decoder(path, num_bits=128, device=None):
    """
    Load a trained WatermarkDecoder from disk.

    Parameters
    ----------
    path     : str   path to saved decoder weights (.pt file)
    num_bits : int   number of watermark bits (default 128)
    device   : str   'cpu', 'cuda', 'mps', or None (auto-detect)

    Returns
    -------
    decoder : WatermarkDecoder   ready for inference
    """
    if device is None:
        if torch.cuda.is_available():
            device = 'cuda'
        elif torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'

    decoder = WatermarkDecoder(num_bits=num_bits)
    decoder.load_weights(path, device=device)
    decoder = decoder.to(device)
    decoder.eval()
    return decoder


# ─────────────────────────────────────────────────────────────────────────────
# Main extraction function
# ─────────────────────────────────────────────────────────────────────────────

def extract_watermark(frame, decoder, return_soft_decisions=True):
    """
    Extract watermark from a frame using the trained CNN decoder.

    Replaces the old correlation-based extract_watermark().
    The interface is identical so existing code that calls
    extract_watermark() works without modification.

    Parameters
    ----------
    frame                : np.ndarray, shape (H, W, 3), dtype uint8
    decoder              : WatermarkDecoder   trained decoder
    return_soft_decisions: bool
        If True  → return soft decisions (probabilities) for LDPC
        If False → return hard bits {0, 1}

    Returns
    -------
    bits_or_probs : np.ndarray, shape (128,)
    confidence    : float in [0, 1]
    """
    soft_bits, confidence = decoder.forward_numpy(frame)

    if return_soft_decisions:
        return soft_bits, confidence
    else:
        return (soft_bits > 0.5).astype(int), confidence