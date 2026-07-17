"""
Phase 3 Tests — Temporal Synchronization

Tests the state machine key generator, temporal matching module,
and temporally-synchronized video watermarking.

Run with: python -m pytest tests/test_temporal.py -v
"""

import numpy as np
import pyldpc
import pytest


def _make_test_ldpc(n=128):
    """Build a deterministic test H/G matrix without production artifacts."""
    np.random.seed(0)
    H, G = pyldpc.make_ldpc(n, 2, 4, systematic=True, sparse=True)
    k = G.shape[1]
    return H, G, k


def make_test_frame(h=128, w=128, seed=0):
    """Create a test frame with texture (not flat)."""
    rng = np.random.RandomState(seed)
    x = np.linspace(0, 255, w).reshape(1, -1).repeat(h, axis=0)
    y = np.linspace(0, 255, h).reshape(-1, 1).repeat(w, axis=1)
    img = np.stack([(x + y) / 2, x, 255 - y], axis=2)
    img += rng.randn(h, w, 3) * 15
    return np.clip(img, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# 3.1: Visual Feature Extractor
# ---------------------------------------------------------------------------

class TestFeatureExtractor:
    """Test robust visual feature extraction."""

    def test_extract_returns_array(self):
        from omni_lock.state_machine import VisualFeatureExtractor
        fe = VisualFeatureExtractor(block_size=32)
        frame = make_test_frame(128, 128, seed=0)
        features = fe.extract(frame)
        assert isinstance(features, np.ndarray)
        assert len(features) > 0

    def test_deterministic(self):
        """Same frame → same features."""
        from omni_lock.state_machine import VisualFeatureExtractor
        fe = VisualFeatureExtractor(block_size=32)
        frame = make_test_frame(128, 128, seed=0)
        f1 = fe.extract(frame)
        f2 = fe.extract(frame)
        np.testing.assert_array_equal(f1, f2)

    def test_different_frames_give_different_features(self):
        from omni_lock.state_machine import VisualFeatureExtractor
        fe = VisualFeatureExtractor(block_size=32)
        # Use larger images with very different content to ensure
        # quantized features differ
        frame1 = np.zeros((256, 256, 3), dtype=np.uint8)  # Black
        frame2 = np.full((256, 256, 3), 255, dtype=np.uint8)  # White
        f1 = fe.extract(frame1)
        f2 = fe.extract(frame2)
        assert not np.array_equal(f1, f2)

    def test_feature_hash_deterministic(self):
        from omni_lock.state_machine import VisualFeatureExtractor
        fe = VisualFeatureExtractor(block_size=32)
        frame = make_test_frame(128, 128, seed=0)
        features = fe.extract(frame)
        h1 = fe.feature_hash(features)
        h2 = fe.feature_hash(features)
        assert h1 == h2
        assert isinstance(h1, int)


# ---------------------------------------------------------------------------
# 3.2: State Machine Key Generator
# ---------------------------------------------------------------------------

class TestStateMachine:
    """Test the content-dependent state machine."""

    def test_deterministic_with_same_seed(self):
        """Same seed + same frames → same state sequence."""
        from omni_lock.state_machine import StateMachineKeyGen
        frames = [make_test_frame(128, 128, seed=i) for i in range(5)]

        sm1 = StateMachineKeyGen(secret_seed=42)
        sm2 = StateMachineKeyGen(secret_seed=42)

        for frame in frames:
            sm1.transition(frame)
            sm2.transition(frame)

        assert sm1.state == sm2.state

    def test_different_seeds_give_different_states(self):
        from omni_lock.state_machine import StateMachineKeyGen
        frame = make_test_frame(128, 128, seed=0)

        sm1 = StateMachineKeyGen(secret_seed=42)
        sm2 = StateMachineKeyGen(secret_seed=99)

        sm1.transition(frame)
        sm2.transition(frame)

        assert sm1.state != sm2.state

    def test_get_key_returns_int(self):
        from omni_lock.state_machine import StateMachineKeyGen
        sm = StateMachineKeyGen(secret_seed=42)
        key = sm.get_key()
        assert isinstance(key, int)

    def test_get_block_index_in_range(self):
        from omni_lock.state_machine import StateMachineKeyGen
        sm = StateMachineKeyGen(secret_seed=42)
        frames = [make_test_frame(128, 128, seed=i) for i in range(20)]
        for frame in frames:
            sm.transition(frame)
            idx = sm.get_block_index()
            assert 0 <= idx <= 3

    def test_reset_restores_initial_state(self):
        from omni_lock.state_machine import StateMachineKeyGen
        sm = StateMachineKeyGen(secret_seed=42)
        initial = sm.state

        frames = [make_test_frame(128, 128, seed=i) for i in range(5)]
        for frame in frames:
            sm.transition(frame)
        assert sm.state != initial

        sm.reset()
        assert sm.state == initial

    def test_predict_forward_doesnt_modify_state(self):
        from omni_lock.state_machine import StateMachineKeyGen
        sm = StateMachineKeyGen(secret_seed=42)
        frames = [make_test_frame(128, 128, seed=i) for i in range(5)]

        state_before = sm.state
        predicted, keys = sm.predict_forward(frames)
        state_after = sm.state

        assert state_before == state_after
        assert len(predicted) == 5
        assert len(keys) == 5


# ---------------------------------------------------------------------------
# 3.3: Temporal Matching Module (TMM)
# ---------------------------------------------------------------------------

class TestTMM:
    """Test the temporal matching / edit distance alignment."""

    def test_align_perfect_blocks(self):
        """4 blocks with correct indices → perfect alignment."""
        from omni_lock.tmm import align_soft_decisions
        rng = np.random.RandomState(0)

        blocks = []
        for i in range(4):
            blocks.append({
                'soft_bits': rng.random(32),
                'block_idx': i,
                'confidence': 0.9
            })

        aligned, cost = align_soft_decisions(blocks, target_length=128)
        assert aligned.shape == (128,)
        assert cost < 30.0  # Moderate cost for high confidence blocks

    def test_align_with_missing_block(self):
        """3 out of 4 blocks → gaps filled with 0.5."""
        from omni_lock.tmm import align_soft_decisions
        rng = np.random.RandomState(0)

        blocks = []
        for i in [0, 1, 3]:  # Missing block 2
            blocks.append({
                'soft_bits': rng.random(32),
                'block_idx': i,
                'confidence': 0.8
            })

        aligned, cost = align_soft_decisions(blocks, target_length=128)
        assert aligned.shape == (128,)
        # Block 2 region (bits 64-96) should be 0.5
        np.testing.assert_array_equal(aligned[64:96], 0.5)

    def test_edit_distance_same_length(self):
        """Same length input → zero cost, same output."""
        from omni_lock.tmm import align_sequence_edit_distance
        seq = np.random.RandomState(0).random(128)
        aligned, cost = align_sequence_edit_distance(seq, target_length=128)
        assert aligned.shape == (128,)
        assert cost == 0.0
        np.testing.assert_array_almost_equal(aligned, seq)

    def test_edit_distance_shorter_input(self):
        """Shorter input → gaps inserted."""
        from omni_lock.tmm import align_sequence_edit_distance
        seq = np.random.RandomState(0).random(100)
        aligned, cost = align_sequence_edit_distance(seq, target_length=128)
        assert aligned.shape == (128,)
        assert cost > 0.0

    def test_edit_distance_longer_input(self):
        """Longer input → bits deleted."""
        from omni_lock.tmm import align_sequence_edit_distance
        seq = np.random.RandomState(0).random(150)
        aligned, cost = align_sequence_edit_distance(seq, target_length=128)
        assert aligned.shape == (128,)
        assert cost > 0.0


# ---------------------------------------------------------------------------
# 3.4: Temporally-Synchronized Video Embedding
# ---------------------------------------------------------------------------

class TestTemporalVideo:
    """Test the full temporal video watermarking pipeline."""

    def test_embed_returns_correct_count(self):
        from omni_lock.temporal_video import embed_video_temporal

        H, G, k = _make_test_ldpc()
        frames = [make_test_frame(128, 128, seed=i) for i in range(8)]
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)

        watermarked, metadata = embed_video_temporal(
            frames, wm_id, G, k, secret_key=42
        )
        assert len(watermarked) == 8
        assert len(metadata) == 8

    def test_metadata_has_required_fields(self):
        from omni_lock.temporal_video import embed_video_temporal

        H, G, k = _make_test_ldpc()
        frames = [make_test_frame(128, 128, seed=i) for i in range(4)]
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)

        _, metadata = embed_video_temporal(frames, wm_id, G, k)
        for m in metadata:
            assert 'frame_idx' in m
            assert 'state' in m
            assert 'key' in m
            assert 'block_idx' in m
            assert 0 <= m['block_idx'] <= 3

    def test_extract_returns_correct_shape(self):
        from omni_lock.temporal_video import (
            embed_video_temporal, extract_video_temporal
        )

        H, G, k = _make_test_ldpc()
        frames = [make_test_frame(128, 128, seed=i) for i in range(8)]
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)

        watermarked, _ = embed_video_temporal(
            frames, wm_id, G, k, secret_key=42
        )
        decoded, success, info = extract_video_temporal(
            watermarked, H, G=G, secret_key=42
        )
        assert decoded.shape == (64,)
        assert isinstance(success, (bool, np.bool_))
        assert 'num_frames_processed' in info

    def test_simulate_frame_drop(self):
        from omni_lock.temporal_video import simulate_frame_drop
        frames = [make_test_frame(64, 64, seed=i) for i in range(8)]
        attacked = simulate_frame_drop(frames, drop_indices=[1, 3])
        assert len(attacked) == 6

    def test_simulate_frame_swap(self):
        from omni_lock.temporal_video import simulate_frame_swap
        frames = [make_test_frame(64, 64, seed=i) for i in range(8)]
        original_0 = frames[0].copy()
        original_1 = frames[1].copy()

        swapped = simulate_frame_swap(frames, swap_pairs=[(0, 1)])
        np.testing.assert_array_equal(swapped[0], original_1)
        np.testing.assert_array_equal(swapped[1], original_0)

    def test_extract_needs_min_frames(self):
        from omni_lock.temporal_video import extract_video_temporal

        H, G, k = _make_test_ldpc()
        frames = [make_test_frame(64, 64, seed=0)]

        with pytest.raises(ValueError, match="at least"):
            extract_video_temporal(frames, H, G=G, min_frames=4)
