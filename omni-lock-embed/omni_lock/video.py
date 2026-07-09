"""
4-Frame Video Interleaving

Spreads the 128-bit LDPC codeword across 4 consecutive frames
(32 bits per frame), enabling watermark detection from short clips
like TikTok/Reels/Shorts.

Embedding:
  128-bit codeword → split into 4×32 bits → embed one block per frame

Extraction:
  4 frames → extract 32 soft decisions each → concatenate → LDPC decode
"""

import numpy as np

from .embedder import embed_watermark
from .extractor import extract_watermark
from .ldpc import ldpc_encode, ldpc_decode_soft


def embed_video(video_frames, watermark_id_64bit, G, k,
                secret_key=42, alpha=0.1):
    """
    Embed watermark across video with 4-frame interleaving.

    Parameters
    ----------
    video_frames : list of np.ndarray
        List of frames, each shape (H, W, 3), dtype uint8.
    watermark_id_64bit : np.ndarray, shape (64,)
        Binary watermark ID.
    G : np.ndarray
        LDPC generator matrix from pyldpc.
    k : int
        Number of information bits for the LDPC code.
    secret_key : int
        Secret key for Mixer network.
    alpha : float
        Embedding strength.

    Returns
    -------
    watermarked_frames : list of np.ndarray
        Watermarked video frames.
    """
    # LDPC encode: 64-bit → 128-bit BPSK codeword
    codeword_bpsk, _ = ldpc_encode(watermark_id_64bit, G, k)

    # Convert BPSK to binary: +1 → 0, -1 → 1
    codeword_binary = (codeword_bpsk < 0).astype(int)

    # Split into 4 blocks of 32 bits
    bit_blocks = [
        codeword_binary[0:32],
        codeword_binary[32:64],
        codeword_binary[64:96],
        codeword_binary[96:128]
    ]

    watermarked_frames = []

    for frame_idx, frame in enumerate(video_frames):
        block_idx = frame_idx % 4
        current_bits = bit_blocks[block_idx]

        # Pad 32 bits → 64 bits for Mixer input
        bits_padded = np.concatenate([current_bits, current_bits])

        # Use a different sub-key per block for diversity
        sub_key = secret_key + block_idx

        wm_frame, _ = embed_watermark(frame, bits_padded, sub_key, alpha)
        watermarked_frames.append(wm_frame)

    return watermarked_frames


def extract_video(video_frames, H, G=None, secret_key=42,
                  temp_scaler=None, min_frames=4):
    """
    Extract watermark from video (needs ≥4 frames).

    Parameters
    ----------
    video_frames : list of np.ndarray
        At least 4 frames from the watermarked video.
    H : np.ndarray
        LDPC parity-check matrix.
    secret_key : int
        Same secret key used during embedding.
    temp_scaler : TemperatureScaling or None
        Optional temperature calibrator.
    min_frames : int
        Minimum frames required (4 for full codeword).

    Returns
    -------
    decoded_id : np.ndarray, shape (64,)
        Recovered watermark ID.
    success : bool
        True if LDPC decoding succeeded.
    """
    if len(video_frames) < min_frames:
        raise ValueError(f"Need at least {min_frames} frames, got {len(video_frames)}")

    soft_blocks = []

    for frame_idx in range(4):
        frame = video_frames[frame_idx]
        sub_key = secret_key + (frame_idx % 4)

        # Extract soft decisions (64 bits, but only first 32 are unique)
        soft_bits, _ = extract_watermark(
            frame, sub_key, num_bits=64,
            return_soft_decisions=True
        )

        # Take first 32 bits (the rest are padding duplicates)
        soft_blocks.append(soft_bits[:32])

    # Concatenate to form 128-bit soft codeword
    soft_codeword_128 = np.concatenate(soft_blocks)

    # Optional temperature calibration
    if temp_scaler is not None:
        soft_codeword_128 = temp_scaler.calibrate(soft_codeword_128)

    # LDPC decode
    decoded_message, success = ldpc_decode_soft(soft_codeword_128, H, G=G, n_message_bits=64)

    return decoded_message, success
