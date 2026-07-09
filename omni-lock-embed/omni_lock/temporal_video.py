"""
Temporally-Synchronized Video Watermarking

Upgrades the static 4-frame interleaving with content-aware
temporal synchronization. Uses the State Machine Key Generator
for embedding-key derivation and the Temporal Matching Module
for robust extraction under frame attacks.

Embedding:
  For each frame → extract visual features → derive state → derive key
  → embed 32-bit block using content-aware key → advance state

Extraction:
  For each frame → queue-based detection → align blocks via TMM
  → LDPC decode with aligned soft decisions
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .flow import SpyNetLite, bilinear_warp
from .embedder import embed_watermark


class DifferentiableHEVCSimulator(nn.Module):
    """
    Differentiable proxy for HEVC inter-prediction.

    Produces X̂_t = f_θ( W(X_{t-1}, v_t) ), where W(·) is a Spatial Transformer
    warp via torch.nn.functional.grid_sample and f_θ is a shallow refinement
    CNN emulating the 8-tap DCT-IF interpolation filter.
    """

    def __init__(self,
                 flow_estimator: nn.Module,
                 refine_channels: int = 32,
                 refine_depth: int = 3):
        super().__init__()
        self.flow_estimator = flow_estimator
        # Refinement CNN: refine_depth × Conv2d(3×3, refine_channels ch)+ReLU + 1×1 Conv2d(→3ch)
        layers: list[nn.Module] = []
        in_ch = 3
        for _ in range(refine_depth):
            layers.append(nn.Conv2d(in_ch, refine_channels, kernel_size=3, padding=1))
            layers.append(nn.ReLU(inplace=True))
            in_ch = refine_channels
        layers.append(nn.Conv2d(refine_channels, 3, kernel_size=1))
        self.refine_cnn = nn.Sequential(*layers)

    def estimate_flow(self, prev: Tensor, curr: Tensor) -> Tensor:
        """prev, curr: (B, C, H, W) in [0, 255]. Returns v_t: (B, 2, H, W)."""
        return self.flow_estimator(prev, curr)

    def warp(self, prev: Tensor, flow: Tensor) -> Tensor:
        """
        Bilinear backward warp via grid_sample. Returns X̃_warp: (B, C, H, W).

        mode='bilinear', padding_mode='border', align_corners=True:
        these three flags together produce the correct gradient w.r.t.
        flow on the boundary.
        """
        return bilinear_warp(prev, flow)

    def refine(self, warped: Tensor) -> Tensor:
        """Refinement CNN emulating DCT-IF sharpness. Returns X̂_t."""
        return self.refine_cnn(warped)

    def forward(self, prev_frame: Tensor, curr_frame: Tensor
                ) -> tuple[Tensor, Tensor, Tensor]:
        """
        Returns
        -------
        x_hat    : (B, C, H, W) — X̂_t
        residual : (B, C, H, W) — R_t = curr_frame − x_hat
        flow     : (B, 2, H, W) — v_t (kept for loss & debugging)
        """
        flow = self.estimate_flow(prev_frame, curr_frame)
        warped = self.warp(prev_frame, flow)
        x_hat = self.refine(warped)
        residual = curr_frame - x_hat
        return x_hat, residual, flow


def embed_video_temporal(video_frames, watermark_id_64bit, G, k,
                         secret_key=42, alpha=0.1):
    """
    Embed watermark across video with temporal synchronization.

    Uses a content-aware state machine to derive per-frame embedding
    keys, replacing static modulo-based block assignment.

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
        Secret key for state machine initialization.
    alpha : float
        Embedding strength.

    Returns
    -------
    watermarked_frames : list of np.ndarray
        Watermarked video frames.
    frame_metadata : list of dict
        Per-frame metadata (state, key, block_idx) for verification.
    """
    from .ldpc import ldpc_encode
    from .state_machine import StateMachineKeyGen

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

    # Initialize state machine
    sm = StateMachineKeyGen(secret_seed=secret_key)

    watermarked_frames = []
    frame_metadata = []

    for frame_idx, frame in enumerate(video_frames):
        # Get content-aware key and block index
        embed_key = sm.get_key()
        block_idx = sm.get_block_index()
        current_bits = bit_blocks[block_idx]

        # Pad 32 bits → 64 bits for Mixer input
        bits_padded = np.concatenate([current_bits, current_bits])

        # Embed using the state-derived key
        wm_frame, _ = embed_watermark(frame, bits_padded, embed_key, alpha)
        watermarked_frames.append(wm_frame)

        # Record metadata
        frame_metadata.append({
            'frame_idx': frame_idx,
            'state': sm.state,
            'key': embed_key,
            'block_idx': block_idx
        })

        # Advance state based on ORIGINAL frame content
        # (must use original frame, not watermarked, for feature stability)
        sm.transition(frame)

    return watermarked_frames, frame_metadata


def extract_video_temporal(video_frames, H, G=None, secret_key=42,
                           temp_scaler=None, min_frames=4):
    """
    Extract watermark from video with temporal synchronization.

    Uses the state machine to predict embedding keys for each frame,
    then aligns extracted soft decisions via the TMM before LDPC decoding.

    Parameters
    ----------
    video_frames : list of np.ndarray
        Video frames (potentially with dropped/swapped frames).
    H : np.ndarray
        LDPC parity-check matrix.
    G : np.ndarray, optional
        LDPC generator matrix.
    secret_key : int
        Same secret key used during embedding.
    temp_scaler : TemperatureScaling or None
        Optional temperature calibrator.
    min_frames : int
        Minimum frames required.

    Returns
    -------
    decoded_id : np.ndarray, shape (64,)
        Recovered watermark ID.
    success : bool
        True if LDPC decoding succeeded.
    extraction_info : dict
        Debug info about extraction process.
    """
    from .ldpc import ldpc_decode_soft
    from .extractor import extract_watermark
    from .state_machine import StateMachineKeyGen
    from .tmm import align_soft_decisions

    if len(video_frames) < min_frames:
        raise ValueError(
            f"Need at least {min_frames} frames, got {len(video_frames)}"
        )

    # Initialize state machine (same seed as embedder)
    sm = StateMachineKeyGen(secret_seed=secret_key)

    # Extract soft decisions from each frame using state-derived keys
    extracted_blocks = []

    for frame_idx, frame in enumerate(video_frames):
        # Predict key for this frame
        embed_key = sm.get_key()
        block_idx = sm.get_block_index()

        # Extract soft decisions using predicted key
        soft_bits, confidence = extract_watermark(
            frame, embed_key, num_bits=64,
            return_soft_decisions=True
        )

        extracted_blocks.append({
            'soft_bits': soft_bits[:32],  # First 32 bits (rest are duplicates)
            'block_idx': block_idx,
            'confidence': float(confidence),
            'frame_idx': frame_idx,
            'key': embed_key
        })

        # Advance state machine using frame content
        sm.transition(frame)

    # Align blocks using TMM
    aligned_codeword, alignment_cost = align_soft_decisions(
        extracted_blocks, target_length=128
    )

    # Optional temperature calibration
    if temp_scaler is not None:
        aligned_codeword = temp_scaler.calibrate(aligned_codeword)

    # LDPC decode
    decoded_message, success = ldpc_decode_soft(
        aligned_codeword, H, G=G, n_message_bits=64
    )

    extraction_info = {
        'num_frames_processed': len(video_frames),
        'alignment_cost': alignment_cost,
        'block_confidences': [b['confidence'] for b in extracted_blocks],
        'blocks_found': len(extracted_blocks)
    }

    return decoded_message, success, extraction_info


def simulate_frame_drop(frames, drop_indices):
    """
    Simulate a frame dropping attack.

    Parameters
    ----------
    frames : list of np.ndarray
        Original video frames.
    drop_indices : list of int
        Indices of frames to drop.

    Returns
    -------
    attacked_frames : list of np.ndarray
        Frames with specified indices removed.
    """
    return [f for i, f in enumerate(frames) if i not in drop_indices]


def simulate_frame_swap(frames, swap_pairs):
    """
    Simulate a frame swapping attack.

    Parameters
    ----------
    frames : list of np.ndarray
        Original video frames.
    swap_pairs : list of tuple
        Each (i, j) specifies frames to swap.

    Returns
    -------
    attacked_frames : list of np.ndarray
        Frames with specified pairs swapped.
    """
    result = list(frames)
    for i, j in swap_pairs:
        if i < len(result) and j < len(result):
            result[i], result[j] = result[j], result[i]
    return result


def embed_video_residual(
    video_frames: Tensor,
    watermark_id_64bit: Tensor,
    generator: nn.Module,
    simulator: 'DifferentiableHEVCSimulator',
    embedder: 'ResidualEmbedder',
    G: 'np.ndarray',
    k: int,
    secret_key: int = 42,
) -> tuple[Tensor, list[dict]]:
    """
    Residual-domain analogue of embed_video_temporal().

    Frame t=0 is treated as an I-frame: embedded via the existing 2D
    DifferentiableDCTEmbedder path.  Frames t≥1 go through the
    simulator+residual path (X̂_t + R_t + α·M_t).

    The state-machine block-index logic is preserved verbatim from
    embed_video_temporal(); only the per-frame embed call is swapped.

    Parameters
    ----------
    video_frames          : (T, C, H, W) float32 in [0, 255]
    watermark_id_64bit    : (64,) binary tensor
    generator             : raw-mask producer (MixerTorch / ViViT)
    simulator             : DifferentiableHEVCSimulator instance
    embedder              : ResidualEmbedder instance
    G                     : LDPC generator matrix (numpy)
    k                     : number of LDPC information bits
    secret_key            : state-machine seed

    Returns
    -------
    watermarked_frames : (T, C, H, W) float32, clamped to [0, 255]
    frame_metadata     : list of per-frame dicts (state, key, block_idx, …)
    """
    from .ldpc import ldpc_encode
    from .state_machine import StateMachineKeyGen
    from .dct_torch import DifferentiableDCTEmbedder
    from .embedder import ResidualEmbedder as _ResidualEmbedder

    T, C, H, W = video_frames.shape

    # LDPC encode: 64-bit → 128-bit BPSK codeword
    wm_np = watermark_id_64bit.cpu().numpy()
    codeword_bpsk, _ = ldpc_encode(wm_np, G, k)
    codeword_binary = (codeword_bpsk < 0).astype(int)

    bit_blocks_np = [
        codeword_binary[0:32],
        codeword_binary[32:64],
        codeword_binary[64:96],
        codeword_binary[96:128],
    ]
    # Convert to float tensors once
    bit_blocks = [
        torch.tensor(b, dtype=torch.float32, device=video_frames.device)
        for b in bit_blocks_np
    ]

    sm = StateMachineKeyGen(secret_seed=secret_key)
    dct_embedder = DifferentiableDCTEmbedder(
        block_size=embedder.block_size, alpha=embedder.alpha
    ).to(video_frames.device)

    watermarked = []
    frame_metadata: list[dict] = []

    for t in range(T):
        embed_key = sm.get_key()
        block_idx = sm.get_block_index()
        current_bits = bit_blocks[block_idx]  # (32,) float tensor

        # Pad 32 bits → 64 bits for generator input
        bits_padded = torch.cat([current_bits, current_bits], dim=0).unsqueeze(0)  # (1, 64)

        # Generator produces raw mask M̃_t
        mask_flat = generator(bits_padded)  # (1, spatial_dim) or (1, C, H, W)
        if mask_flat.dim() == 2:
            # Reshape flat → spatial, replicate across channels
            mask_spatial = mask_flat.view(1, 1, H, W).expand(1, C, H, W)
        else:
            mask_spatial = mask_flat  # already (1, C, H, W)

        curr_frame = video_frames[t:t+1]  # (1, C, H, W)

        if t == 0:
            # I-frame: embed via 2D DCT path (spatial_mask averaged across channels)
            mask_2d = mask_spatial.mean(dim=1)  # (1, H, W)
            wm_frame = dct_embedder(curr_frame, mask_2d)
        else:
            # P-frame: residual-domain Wyner-Ziv embedding
            prev_frame = watermarked[t - 1]
            x_hat, residual, flow = simulator(prev_frame, curr_frame)
            wm_frame, _ = embedder(x_hat, residual, mask_spatial)

        watermarked.append(wm_frame)

        frame_metadata.append({
            'frame_idx': t,
            'state': sm.state,
            'key': embed_key,
            'block_idx': block_idx,
        })

        # Advance state based on ORIGINAL (un-watermarked) frame content
        # Use numpy uint8 as required by StateMachineKeyGen.transition
        frame_np = curr_frame.squeeze(0).permute(1, 2, 0).clamp(0, 255).byte().cpu().numpy()
        sm.transition(frame_np)

    watermarked_tensor = torch.cat(watermarked, dim=0)  # (T, C, H, W)
    return watermarked_tensor, frame_metadata
