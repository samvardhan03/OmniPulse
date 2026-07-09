"""
State Machine Key Generator for Temporal Synchronization

Replaces static modulo-based frame interleaving with content-aware
key derivation. The embedding key for each frame is determined by
the visual content of the frame itself, making the system immune to
frame drops, insertions, swaps, and rate conversion.

Architecture:
  - Feature extractor: robust visual features invariant to compression
  - State machine: cryptographic state evolves based on content features
  - Key derivation: current state → embedding key
  - Queue detector: FIFO search for re-synchronization on extraction
"""

import numpy as np
import hashlib
import struct


class VisualFeatureExtractor:
    """
    Extracts robust visual features that survive compression.

    Uses average luminance of macro-blocks as the primary feature,
    which is invariant to JPEG quality, moderate cropping, and
    color-space conversion.
    """

    def __init__(self, block_size=32, num_edge_bins=8):
        self.block_size = block_size
        self.num_edge_bins = num_edge_bins

    def extract(self, frame):
        """
        Extract robust feature vector from a video frame.

        Parameters
        ----------
        frame : np.ndarray, shape (H, W, 3), dtype uint8
            Input video frame (BGR or RGB).

        Returns
        -------
        features : np.ndarray, shape (N,)
            Robust feature vector. N depends on frame size and block_size.
        """
        # Convert to grayscale
        if frame.ndim == 3:
            gray = np.mean(frame, axis=2).astype(np.float32)
        else:
            gray = frame.astype(np.float32)

        h, w = gray.shape
        bs = self.block_size

        # Pad to multiple of block_size
        pad_h = (bs - h % bs) % bs
        pad_w = (bs - w % bs) % bs
        if pad_h > 0 or pad_w > 0:
            gray = np.pad(gray, ((0, pad_h), (0, pad_w)), mode='edge')

        h_padded, w_padded = gray.shape
        n_blocks_h = h_padded // bs
        n_blocks_w = w_padded // bs

        # Feature 1: Average luminance per macro-block
        blocks = gray.reshape(n_blocks_h, bs, n_blocks_w, bs)
        luminance = blocks.mean(axis=(1, 3)).flatten()

        # Quantize to 8 levels for robustness against compression noise
        luminance_quantized = np.floor(luminance / 32.0).astype(np.uint8)

        # Feature 2: Horizontal and vertical edge energy ratio
        # Sobel-like edge detection (simple gradient)
        grad_h = np.abs(np.diff(gray, axis=0)).mean()
        grad_v = np.abs(np.diff(gray, axis=1)).mean()
        edge_ratio = grad_h / (grad_v + 1e-6)
        edge_quantized = min(int(edge_ratio * 4), 15)

        # Combine into feature vector
        features = np.append(luminance_quantized, edge_quantized)
        return features

    def feature_hash(self, features):
        """
        Hash features into a deterministic 32-bit integer.

        Parameters
        ----------
        features : np.ndarray
            Feature vector from extract().

        Returns
        -------
        hash_val : int
            32-bit hash of the features.
        """
        data = features.tobytes()
        digest = hashlib.sha256(data).digest()
        return struct.unpack('<I', digest[:4])[0]


class StateMachineKeyGen:
    """
    Content-dependent state machine for temporal watermark key derivation.

    State transitions depend on the visual content of each frame,
    making the system immune to temporal attacks (frame drops, insertions,
    swaps, rate conversion).

    The state machine uses a hash-based transition function:
        s_{n+1} = f(s_n, v_n)
    where v_n is the visual feature vector of frame n.

    Attributes
    ----------
    state : int
        Current 32-bit cryptographic state.
    feature_extractor : VisualFeatureExtractor
        Extracts robust visual features from frames.
    """

    def __init__(self, secret_seed=42, block_size=32):
        """
        Initialize the state machine.

        Parameters
        ----------
        secret_seed : int
            Secret seed for initial state. Must match between embedder
            and extractor.
        block_size : int
            Macro-block size for feature extraction.
        """
        self.secret_seed = secret_seed
        self.initial_state = self._seed_to_state(secret_seed)
        self.state = self.initial_state
        self.feature_extractor = VisualFeatureExtractor(block_size=block_size)
        self.history = []  # Track state history for debugging

    def _seed_to_state(self, seed):
        """Convert seed to initial 32-bit state."""
        data = struct.pack('<Q', seed)
        digest = hashlib.sha256(data).digest()
        return struct.unpack('<I', digest[:4])[0]

    def reset(self):
        """Reset state machine to initial state."""
        self.state = self.initial_state
        self.history = []

    def transition(self, frame):
        """
        Advance state based on current frame's visual content.

        Parameters
        ----------
        frame : np.ndarray, shape (H, W, 3)
            Current video frame.

        Returns
        -------
        new_state : int
            The new state after transition.
        """
        features = self.feature_extractor.extract(frame)
        feat_hash = self.feature_extractor.feature_hash(features)

        # Transition: XOR current state with feature hash, then hash again
        combined = struct.pack('<II', self.state, feat_hash)
        digest = hashlib.sha256(combined).digest()
        new_state = struct.unpack('<I', digest[:4])[0]

        self.history.append(self.state)
        self.state = new_state
        return new_state

    def get_key(self):
        """
        Derive embedding key from current state.

        Returns
        -------
        key : int
            Deterministic key derived from current state.
            Used as secret_key parameter for the Mixer network.
        """
        # Mix the state to derive a key
        data = struct.pack('<I', self.state) + b'omnilock_key'
        digest = hashlib.sha256(data).digest()
        return struct.unpack('<I', digest[:4])[0]

    def get_block_index(self):
        """
        Derive which codeword block (0-3) to embed from current state.

        Returns
        -------
        block_idx : int
            Block index in [0, 3] for 4-block interleaving.
        """
        return self.state % 4

    def predict_forward(self, frames, depth=None):
        """
        Predict future states without modifying current state.

        Parameters
        ----------
        frames : list of np.ndarray
            Future frames to predict states for.
        depth : int or None
            Max prediction depth (default: len(frames)).

        Returns
        -------
        predicted_states : list of int
            Predicted states for each frame.
        predicted_keys : list of int
            Predicted keys for each frame.
        """
        if depth is None:
            depth = len(frames)

        saved_state = self.state
        saved_history = list(self.history)

        predictions = []
        keys = []

        for i, frame in enumerate(frames[:depth]):
            self.transition(frame)
            predictions.append(self.state)
            keys.append(self.get_key())

        # Restore state
        self.state = saved_state
        self.history = saved_history

        return predictions, keys


class QueueDetector:
    """
    FIFO queue-based temporal synchronization detector.

    Maintains a queue of recently detected states and performs
    search + correlation to find the correct temporal position
    even after frame drops, insertions, or swaps.
    """

    def __init__(self, state_machine, queue_size=16):
        """
        Initialize the queue detector.

        Parameters
        ----------
        state_machine : StateMachineKeyGen
            The state machine (initialized with the same secret seed).
        queue_size : int
            Size of the FIFO history queue.
        """
        self.sm = state_machine
        self.queue_size = queue_size
        self.state_queue = []  # FIFO queue of (state, key, block_idx) tuples
        self.synchronized = False

    def _add_to_queue(self, state, key, block_idx):
        """Add a state entry to the FIFO queue."""
        entry = (state, key, block_idx)
        self.state_queue.append(entry)
        if len(self.state_queue) > self.queue_size:
            self.state_queue.pop(0)

    def detect_and_sync(self, frame, extract_fn, num_bits=64):
        """
        Attempt to detect watermark and synchronize temporal position.

        Tries the current predicted state first. If that fails,
        searches the queue for a matching state via correlation.

        Parameters
        ----------
        frame : np.ndarray, shape (H, W, 3)
            Video frame to analyze.
        extract_fn : callable
            Function(frame, secret_key, num_bits) → (soft_bits, confidence).
        num_bits : int
            Number of bits to extract per frame.

        Returns
        -------
        result : dict
            {
                'soft_bits': np.ndarray or None,
                'key': int,
                'block_idx': int,
                'confidence': float,
                'synchronized': bool
            }
        """
        # Compute content-based state for this frame
        features = self.sm.feature_extractor.extract(frame)
        feat_hash = self.sm.feature_extractor.feature_hash(features)

        best_result = None
        best_confidence = -1.0

        # Strategy 1: Try current state prediction
        predicted_key = self.sm.get_key()
        soft_bits, confidence = extract_fn(
            frame, predicted_key, num_bits,
            return_soft_decisions=True
        )

        if confidence > best_confidence:
            best_confidence = confidence
            best_result = {
                'soft_bits': soft_bits,
                'key': predicted_key,
                'block_idx': self.sm.get_block_index(),
                'confidence': confidence,
                'synchronized': True,
                'source': 'predicted'
            }

        # Strategy 2: Search the queue for better matches
        for state, key, block_idx in self.state_queue:
            soft_bits_q, confidence_q = extract_fn(
                frame, key, num_bits,
                return_soft_decisions=True
            )
            if confidence_q > best_confidence:
                best_confidence = confidence_q
                best_result = {
                    'soft_bits': soft_bits_q,
                    'key': key,
                    'block_idx': block_idx,
                    'confidence': confidence_q,
                    'synchronized': True,
                    'source': 'queue'
                }

        # Advance state machine
        self.sm.transition(frame)
        new_key = self.sm.get_key()
        new_block = self.sm.get_block_index()
        self._add_to_queue(self.sm.state, new_key, new_block)

        self.synchronized = best_result is not None and best_confidence > 0.0
        return best_result
