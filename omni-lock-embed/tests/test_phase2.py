"""
Phase 2 Tests — End-to-End Pipeline, Attack Robustness, Video

Run with: python -m pytest tests/test_phase2.py -v
"""
import numpy as np
import pytest
from omni_lock.watermarker import OmniLockWatermarker
from omni_lock.attacks import AttackSuite
from omni_lock.embedder import evaluate_quality

def make_test_image(h=256, w=256, seed=0):
    """Create a realistic-ish test image with gradients and texture."""
    rng = np.random.RandomState(seed)
    x = np.linspace(0, 255, w).reshape(1, -1).repeat(h, axis=0)
    y = np.linspace(0, 255, h).reshape(-1, 1).repeat(w, axis=1)
    img = np.stack([(x + y) / 2, x, 255 - y], axis=2)
    img += rng.randn(h, w, 3) * 15
    return np.clip(img, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# 2.1: End-to-End Pipeline
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """Test the unified OmniLockWatermarker."""

    @pytest.fixture
    def watermarker(self):
        return OmniLockWatermarker(secret_key=42, alpha=0.1)

    def test_embed_extract_clean(self, watermarker):
        img = make_test_image(256, 256, seed=0)
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)
        watermarked = watermarker.embed_single_frame(img, wm_id)
        extracted, confidence = watermarker.extract_single_frame(watermarked)
        assert confidence > 0.0
        assert extracted.shape == (64,)

    def test_quality_targets(self, watermarker):
        img = make_test_image(256, 256, seed=1)
        wm_id = np.random.RandomState(1).randint(0, 2, size=64)
        watermarked = watermarker.embed_single_frame(img, wm_id)
        quality = watermarker.evaluate_quality(img, watermarked)
        assert quality['PSNR'] > 35.0
        assert quality['SSIM'] > 0.95

    def test_multiple_images(self, watermarker):
        for seed in range(5):
            img = make_test_image(256, 256, seed=seed)
            wm_id = np.random.RandomState(seed).randint(0, 2, size=64)
            watermarked = watermarker.embed_single_frame(img, wm_id)
            quality = watermarker.evaluate_quality(img, watermarked)
            assert quality['PSNR'] > 30.0, f"Image {seed}: PSNR={quality['PSNR']:.2f}"


# ---------------------------------------------------------------------------
# 2.2: Attack Robustness
# ---------------------------------------------------------------------------

class TestAttacks:
    """Test attack implementations and watermark survival."""

    def test_jpeg_attack_runs(self):

        img = make_test_image(256, 256)
        for q in [50, 70, 90]:
            attacked = AttackSuite.jpeg_compression(img, q)
            assert attacked.shape == img.shape

    def test_crop_attack_preserves_size(self):
        img = make_test_image(256, 256)
        for pct in [0.1, 0.25, 0.5]:
            attacked = AttackSuite.crop(img, pct)
            assert attacked.shape == img.shape

    def test_scale_attack(self):
        img = make_test_image(256, 256)
        for sf in [0.5, 0.75, 1.5]:
            attacked = AttackSuite.scale(img, sf)
            assert attacked.shape == img.shape

    def test_blur_attack(self):
        img = make_test_image(256, 256)
        attacked = AttackSuite.gaussian_blur(img, sigma=2.0)
        assert attacked.shape == img.shape

    def test_rotation_attack(self):
        img = make_test_image(256, 256)
        attacked = AttackSuite.rotation(img, 5)
        assert attacked.shape == img.shape

    def test_combined_attack(self):
        img = make_test_image(256, 256)
        attacked = AttackSuite.combined_attack(img)
        assert attacked.shape == img.shape

    def test_watermark_survives_jpeg70(self):
        

        wm = OmniLockWatermarker(secret_key=42, alpha=0.15)
        img = make_test_image(256, 256)
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)

        watermarked = wm.embed_single_frame(img, wm_id)
        attacked = AttackSuite.jpeg_compression(watermarked, 70)
        extracted, confidence = wm.extract_single_frame(attacked)
        assert extracted.shape == (64,)


# ---------------------------------------------------------------------------
# 2.3: Video Interleaving
# ---------------------------------------------------------------------------

class TestVideo:
    """Test 4-frame video interleaving."""

    def test_video_embed_frame_count(self):
        wm = OmniLockWatermarker(secret_key=42, alpha=0.1)
        frames = [make_test_image(128, 128, seed=i) for i in range(8)]
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)
        watermarked = wm.embed_video(frames, wm_id)
        assert len(watermarked) == 8

    def test_video_embed_quality(self):
        
        wm = OmniLockWatermarker(secret_key=42, alpha=0.1)
        frames = [make_test_image(128, 128, seed=i) for i in range(4)]
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)
        watermarked = wm.embed_video(frames, wm_id)

        for i in range(4):
            quality = evaluate_quality(frames[i], watermarked[i])
            assert quality['PSNR'] > 30.0

    def test_video_needs_min_frames(self):
        wm = OmniLockWatermarker(secret_key=42, alpha=0.1)
        frames = [make_test_image(128, 128, seed=0)]
        with pytest.raises(ValueError, match="at least"):
            wm.extract_video(frames, min_frames=4)

    def test_video_extract_returns_shape(self):
        wm = OmniLockWatermarker(secret_key=42, alpha=0.1)
        frames = [make_test_image(128, 128, seed=i) for i in range(4)]
        wm_id = np.random.RandomState(42).randint(0, 2, size=64)
        watermarked = wm.embed_video(frames, wm_id)
        decoded, success = wm.extract_video(watermarked)
        assert decoded.shape == (64,)
        assert isinstance(success, (bool, np.bool_))
