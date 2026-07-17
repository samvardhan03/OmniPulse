"""
Phase 1 Tests — Mixer, DCT Embedder, Extractor, LDPC

Run with: python -m pytest tests/test_phase1.py -v
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


# ---------------------------------------------------------------------------
# Test 1.1: Mixer Network
# ---------------------------------------------------------------------------

class TestMixer:
    """Test MLP-Mixer spatial spreading."""

    def test_output_shape(self):
        from omni_lock.mixer import MixerNetwork
        mixer = MixerNetwork(input_dim=64, output_shape=(256, 256), secret_key=42)
        wm = np.random.randint(0, 2, size=64).astype(np.float32)
        mask = mixer.forward(wm)
        assert mask.shape == (256, 256)

    def test_output_range(self):
        """Output should be in [-1, 1] due to tanh."""
        from omni_lock.mixer import MixerNetwork
        mixer = MixerNetwork(input_dim=64, output_shape=(128, 128), secret_key=42)
        wm = np.random.randint(0, 2, size=64).astype(np.float32)
        mask = mixer.forward(wm)
        assert np.all(mask >= -1.0) and np.all(mask <= 1.0)

    def test_deterministic_with_same_key(self):
        """Same key + same watermark → same mask."""
        from omni_lock.mixer import MixerNetwork
        wm = np.array([1, 0] * 32, dtype=np.float32)
        mixer1 = MixerNetwork(input_dim=64, output_shape=(128, 128), secret_key=99)
        mixer2 = MixerNetwork(input_dim=64, output_shape=(128, 128), secret_key=99)
        np.testing.assert_array_equal(mixer1.forward(wm), mixer2.forward(wm))

    def test_different_keys_give_different_masks(self):
        from omni_lock.mixer import MixerNetwork
        wm = np.array([1, 0] * 32, dtype=np.float32)
        mixer1 = MixerNetwork(input_dim=64, output_shape=(128, 128), secret_key=1)
        mixer2 = MixerNetwork(input_dim=64, output_shape=(128, 128), secret_key=2)
        assert not np.allclose(mixer1.forward(wm), mixer2.forward(wm))

    def test_different_watermarks_give_different_masks(self):
        from omni_lock.mixer import MixerNetwork
        mixer = MixerNetwork(input_dim=64, output_shape=(128, 128), secret_key=42)
        wm1 = np.zeros(64, dtype=np.float32)
        wm2 = np.ones(64, dtype=np.float32)
        assert not np.allclose(mixer.forward(wm1), mixer.forward(wm2))


# ---------------------------------------------------------------------------
# Test 1.1: DCT Embedder
# ---------------------------------------------------------------------------

class TestEmbedder:
    """Test DCT watermark embedding and quality metrics."""

    @pytest.fixture
    def sample_image(self):
        rng = np.random.RandomState(0)
        h, w = 256, 256
        x = np.linspace(0, 255, w).reshape(1, -1).repeat(h, axis=0)
        y = np.linspace(0, 255, h).reshape(-1, 1).repeat(w, axis=1)
        img = np.stack([(x + y) / 2, x, y], axis=2)
        img += rng.randn(h, w, 3) * 20
        return np.clip(img, 0, 255).astype(np.uint8)

    @pytest.fixture
    def watermark(self):
        return np.random.RandomState(42).randint(0, 2, size=64)

    def test_embed_preserves_shape(self, sample_image, watermark):
        from omni_lock.embedder import embed_watermark
        wm_frame, mask = embed_watermark(sample_image, watermark, secret_key=42)
        assert wm_frame.shape == sample_image.shape
        assert wm_frame.dtype == np.uint8

    def test_psnr_above_35(self, sample_image, watermark):
        from omni_lock.embedder import embed_watermark, evaluate_quality
        wm_frame, _ = embed_watermark(sample_image, watermark, secret_key=42, alpha=0.1)
        quality = evaluate_quality(sample_image, wm_frame)
        assert quality['PSNR'] > 35.0, f"PSNR={quality['PSNR']:.2f} dB (need >35)"

    def test_ssim_above_095(self, sample_image, watermark):
        from omni_lock.embedder import embed_watermark, evaluate_quality
        wm_frame, _ = embed_watermark(sample_image, watermark, secret_key=42, alpha=0.1)
        quality = evaluate_quality(sample_image, wm_frame)
        assert quality['SSIM'] > 0.95, f"SSIM={quality['SSIM']:.4f} (need >0.95)"

    def test_stronger_alpha_lowers_quality(self, sample_image, watermark):
        from omni_lock.embedder import embed_watermark, evaluate_quality
        wm_low, _ = embed_watermark(sample_image, watermark, secret_key=42, alpha=0.05)
        wm_high, _ = embed_watermark(sample_image, watermark, secret_key=42, alpha=0.2)
        q_low = evaluate_quality(sample_image, wm_low)
        q_high = evaluate_quality(sample_image, wm_high)
        assert q_low['PSNR'] > q_high['PSNR']

    def test_non_square_image(self, watermark):
        from omni_lock.embedder import embed_watermark
        img = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        wm_frame, mask = embed_watermark(img, watermark, secret_key=42)
        assert wm_frame.shape == img.shape


# ---------------------------------------------------------------------------
# Test 1.2: Extractor
# ---------------------------------------------------------------------------

class TestExtractor:
    """Test watermark extraction with soft decisions."""

    @pytest.fixture
    def embedded_pair(self):
        from omni_lock.embedder import embed_watermark
        rng = np.random.RandomState(0)
        img = np.clip(rng.randn(128, 128, 3) * 50 + 128, 0, 255).astype(np.uint8)
        wm = rng.randint(0, 2, size=64)
        wm_frame, _ = embed_watermark(img, wm, secret_key=42, alpha=0.15)
        return wm_frame, wm

    def test_extraction_returns_correct_shape(self, embedded_pair):
        from omni_lock.extractor import extract_watermark
        wm_frame, _ = embedded_pair
        soft, conf = extract_watermark(wm_frame, secret_key=42, return_soft_decisions=True)
        assert soft.shape == (64,)
        assert 0 <= conf <= 1

    def test_soft_decisions_in_range(self, embedded_pair):
        from omni_lock.extractor import extract_watermark
        wm_frame, _ = embedded_pair
        soft, _ = extract_watermark(wm_frame, secret_key=42, return_soft_decisions=True)
        assert np.all(soft >= 0.0) and np.all(soft <= 1.0)

    def test_hard_decision_mode(self, embedded_pair):
        from omni_lock.extractor import extract_watermark
        wm_frame, _ = embedded_pair
        hard, conf = extract_watermark(wm_frame, secret_key=42, return_soft_decisions=False)
        assert set(np.unique(hard)).issubset({0, 1})


# ---------------------------------------------------------------------------
# Test 1.3: LDPC Error Correction (using pyldpc)
# ---------------------------------------------------------------------------

class TestLDPC:
    """Test LDPC encoding/decoding and temperature calibration."""

    def test_encode_produces_valid_codeword(self):
        from omni_lock.ldpc import ldpc_encode
        H, G, k = _make_test_ldpc()
        msg = np.random.RandomState(0).randint(0, 2, size=64)

        codeword_bpsk, padded = ldpc_encode(msg, G, k)
        assert codeword_bpsk.shape == (128,)
        # BPSK values should be ±1
        assert np.all(np.isin(np.sign(codeword_bpsk), [-1, 1]))

    def test_decode_noiseless(self):
        """Perfect soft decisions → perfect decode."""
        from omni_lock.ldpc import ldpc_encode, ldpc_decode_soft
        H, G, k = _make_test_ldpc()
        msg = np.random.RandomState(0).randint(0, 2, size=64)
        codeword_bpsk, padded = ldpc_encode(msg, G, k)

        # Convert BPSK to probabilities: +1 → bit=0 → prob=0.05, -1 → bit=1 → prob=0.95
        soft = np.where(codeword_bpsk > 0, 0.05, 0.95)
        decoded, success = ldpc_decode_soft(soft, H)
        assert success, "Noiseless decode should succeed"
        np.testing.assert_array_equal(decoded[:64], msg)

    def test_decode_with_moderate_noise(self):
        """Should recover with moderate noise."""
        from omni_lock.ldpc import ldpc_encode, ldpc_decode_soft
        H, G, k = _make_test_ldpc()
        rng = np.random.RandomState(1)
        successes = 0
        trials = 20

        for _ in range(trials):
            msg = rng.randint(0, 2, size=64)
            codeword_bpsk, _ = ldpc_encode(msg, G, k)

            # Add AWGN noise
            noise = rng.randn(128) * 0.5
            noisy = codeword_bpsk + noise

            # Convert noisy BPSK to probabilities
            # noisy > 0 → likely bit=0 → low prob
            # noisy < 0 → likely bit=1 → high prob
            soft = 1.0 / (1.0 + np.exp(2 * noisy))  # Sigmoid conversion

            decoded, success = ldpc_decode_soft(soft, H)
            if success and np.array_equal(decoded[:64], msg):
                successes += 1

        success_rate = successes / trials
        assert success_rate > 0.7, f"Success rate {success_rate:.2f} at moderate noise (need >0.7)"

    def test_temperature_scaling(self):
        from omni_lock.ldpc import TemperatureScaling
        ts = TemperatureScaling()

        rng = np.random.RandomState(42)
        true_bits = rng.randint(0, 2, size=(50, 64)).astype(float)
        soft = np.where(true_bits == 1, 0.99, 0.01)
        noise = rng.randn(50, 64) * 0.3
        soft = np.clip(soft + noise, 0.01, 0.99)

        ts.fit(soft, true_bits)
        assert 0.1 <= ts.temperature <= 10.0
        calibrated = ts.calibrate(soft)
        assert calibrated.shape == soft.shape
        assert np.all(calibrated >= 0) and np.all(calibrated <= 1)
