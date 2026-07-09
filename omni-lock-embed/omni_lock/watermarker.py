"""
OmniLockWatermarker — Unified Watermarking System

Integrates all components into a single class:
  Embedding:  64-bit ID → LDPC encode → Mixer → DCT → Frame
  Extraction: Frame → DCT → Correlate → Soft decisions → LDPC decode → 64-bit ID

Supports both single-frame and 4-frame video modes.
"""

import numpy as np

from .embedder import embed_watermark, evaluate_quality
from .extractor import extract_watermark
from .ldpc import create_ldpc_code, ldpc_encode, ldpc_decode_soft, TemperatureScaling
from .video import embed_video, extract_video


class OmniLockWatermarker:
    """
    Complete watermarking system for images and video.

    Parameters
    ----------
    secret_key : int
        Secret key for Mixer network weight initialization.
    alpha : float
        Embedding strength (0.05–0.2). Higher = more robust but more visible.
    """

    def __init__(self, secret_key=42, alpha=0.1):
        self.key = secret_key
        self.alpha = alpha

        # Create LDPC code via pyldpc
        self.H, self.G, self.k = create_ldpc_code(n=128, d_v=2, d_c=4)

        # Temperature calibration (will be fit on validation data)
        self.temp_scaler = TemperatureScaling()

    # ------------------------------------------------------------------
    # Single-frame mode
    # ------------------------------------------------------------------

    def embed_single_frame(self, frame, watermark_id_64bit):
        """
        Embed 64-bit watermark into a single frame.

        Parameters
        ----------
        frame : np.ndarray, shape (H, W, 3), dtype uint8
        watermark_id_64bit : np.ndarray, shape (64,)

        Returns
        -------
        watermarked : np.ndarray, shape (H, W, 3), dtype uint8
        """
        # Embed the raw 64-bit watermark via DCT
        watermarked, _ = embed_watermark(
            frame, watermark_id_64bit, self.key, self.alpha
        )
        return watermarked

    def extract_single_frame(self, frame, use_ldpc=False):
        """
        Extract watermark from a single frame.

        Parameters
        ----------
        frame : np.ndarray, shape (H, W, 3), dtype uint8
        use_ldpc : bool
            Whether to apply LDPC decoding.

        Returns
        -------
        extracted_bits : np.ndarray, shape (64,)
        confidence : float in [0, 1]
        """
        soft_bits, confidence = extract_watermark(
            frame, self.key, num_bits=64,
            return_soft_decisions=True
        )

        if not use_ldpc:
            hard_bits = (soft_bits > 0.5).astype(int)
            return hard_bits, confidence

        # For single-frame LDPC: tile 64 soft decisions → 128
        soft_128 = np.zeros(128)
        soft_128[:64] = soft_bits
        soft_128[64:] = 0.5  # No info for parity bits
        calibrated = self.temp_scaler.calibrate(soft_128)
        decoded, success = ldpc_decode_soft(calibrated, self.H, G=self.G, n_message_bits=64)
        return decoded, confidence

    # ------------------------------------------------------------------
    # Video mode (4-frame interleaving)
    # ------------------------------------------------------------------

    def embed_video(self, video_frames, watermark_id_64bit):
        """
        Embed watermark across video with 4-frame interleaving.

        Parameters
        ----------
        video_frames : list of np.ndarray
        watermark_id_64bit : np.ndarray, shape (64,)

        Returns
        -------
        watermarked_frames : list of np.ndarray
        """
        return embed_video(
            video_frames, watermark_id_64bit,
            self.G, self.k, self.key, self.alpha
        )

    def extract_video(self, video_frames, min_frames=4):
        """
        Extract watermark from video (needs ≥4 frames).

        Parameters
        ----------
        video_frames : list of np.ndarray
        min_frames : int

        Returns
        -------
        decoded_id : np.ndarray, shape (64,)
        success : bool
        """
        return extract_video(
            video_frames, self.H, G=self.G, secret_key=self.key,
            temp_scaler=self.temp_scaler, min_frames=min_frames
        )

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def train_calibration(self, frames, watermark_ids):
        """
        Train temperature scaling on validation data.

        Parameters
        ----------
        frames : list of np.ndarray
        watermark_ids : list of np.ndarray, each shape (64,)
        """
        all_soft = []
        all_true = []

        for frame, true_id in zip(frames, watermark_ids):
            watermarked = self.embed_single_frame(frame, true_id)
            soft_bits, _ = extract_watermark(
                watermarked, self.key, num_bits=64,
                return_soft_decisions=True
            )
            all_soft.append(soft_bits)
            all_true.append(true_id)

        all_soft = np.array(all_soft)
        all_true = np.array(all_true)
        self.temp_scaler.fit(all_soft, all_true)

    # ------------------------------------------------------------------
    # Quality evaluation
    # ------------------------------------------------------------------

    @staticmethod
    def evaluate_quality(original, watermarked):
        """Compute PSNR and SSIM between original and watermarked."""
        return evaluate_quality(original, watermarked)
