"""
Attack Suite for Watermark Robustness Testing

Simulates real-world attacks that watermarked content might encounter:
- Compression (JPEG, H.264)
- Geometric transforms (crop, scale, rotation)
- Filtering (Gaussian blur)
- Combined attacks (screenshot → re-encode → share pipeline)
"""

import numpy as np
import cv2


class AttackSuite:
    """Collection of static attack methods for robustness testing."""

    @staticmethod
    def jpeg_compression(image, quality=70):
        """
        JPEG lossy compression.

        Parameters
        ----------
        image : np.ndarray, shape (H, W, 3)
        quality : int
            JPEG quality factor (1–100). Lower = more compression.
        """
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, encoded = cv2.imencode('.jpg', image, encode_param)
        if not success:
            raise RuntimeError("JPEG encoding failed")
        return cv2.imdecode(encoded, cv2.IMREAD_COLOR)

    @staticmethod
    def crop(image, crop_percentage=0.1):
        """
        Random crop that removes crop_percentage of the image area,
        then resize back to original dimensions.

        Parameters
        ----------
        image : np.ndarray, shape (H, W, 3)
        crop_percentage : float
            Fraction of area to remove (0.0–0.9).
        """
        h, w = image.shape[:2]
        keep_ratio = 1.0 - crop_percentage
        keep_h = max(8, int(h * np.sqrt(keep_ratio)))
        keep_w = max(8, int(w * np.sqrt(keep_ratio)))

        start_h = np.random.randint(0, max(1, h - keep_h + 1))
        start_w = np.random.randint(0, max(1, w - keep_w + 1))

        cropped = image[start_h:start_h+keep_h, start_w:start_w+keep_w]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def scale(image, scale_factor=0.5):
        """
        Downscale then upscale (lossy resampling).

        Parameters
        ----------
        image : np.ndarray, shape (H, W, 3)
        scale_factor : float
            Intermediate scale (e.g. 0.5 = halve then double).
        """
        h, w = image.shape[:2]
        new_h = max(8, int(h * scale_factor))
        new_w = max(8, int(w * scale_factor))

        scaled_down = cv2.resize(image, (new_w, new_h),
                                 interpolation=cv2.INTER_LINEAR)
        scaled_up = cv2.resize(scaled_down, (w, h),
                               interpolation=cv2.INTER_LINEAR)
        return scaled_up

    @staticmethod
    def gaussian_blur(image, sigma=1.0):
        """
        Gaussian blur (simulates motion blur / defocus).

        Parameters
        ----------
        image : np.ndarray, shape (H, W, 3)
        sigma : float
            Blur kernel standard deviation.
        """
        return cv2.GaussianBlur(image, (0, 0), sigma)

    @staticmethod
    def rotation(image, angle=5.0):
        """
        Rotate image around center (lossy due to interpolation).

        Parameters
        ----------
        image : np.ndarray, shape (H, W, 3)
        angle : float
            Rotation angle in degrees.
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, M, (w, h))

    @staticmethod
    def gaussian_noise(image, sigma=10.0):
        """
        Additive Gaussian noise.

        Parameters
        ----------
        image : np.ndarray, shape (H, W, 3)
        sigma : float
            Noise standard deviation.
        """
        noise = np.random.randn(*image.shape) * sigma
        noisy = image.astype(np.float32) + noise
        return np.clip(noisy, 0, 255).astype(np.uint8)

    @staticmethod
    def combined_attack(image):
        """
        Worst-case: multiple attacks chained.
        Simulates: Screenshot → Re-encode → Share pipeline.
        """
        image = AttackSuite.crop(image, 0.30)
        image = AttackSuite.jpeg_compression(image, 70)
        image = AttackSuite.scale(image, 0.75)
        return image
