"""
Evaluation Framework

Runs all attacks on test images and computes comprehensive metrics:
- BER (Bit Error Rate)
- Detection confidence
- LDPC decode success
- PSNR / SSIM quality metrics
"""

import numpy as np
import pandas as pd

from .embedder import evaluate_quality
from .attacks import AttackSuite


def get_attack_configs():
    """Return the standard set of attack configurations."""
    return [
        {'name': 'None',       'func': lambda x: x},
        {'name': 'JPEG-50',    'func': lambda x: AttackSuite.jpeg_compression(x, 50)},
        {'name': 'JPEG-70',    'func': lambda x: AttackSuite.jpeg_compression(x, 70)},
        {'name': 'JPEG-90',    'func': lambda x: AttackSuite.jpeg_compression(x, 90)},
        {'name': 'Crop-10%',   'func': lambda x: AttackSuite.crop(x, 0.10)},
        {'name': 'Crop-25%',   'func': lambda x: AttackSuite.crop(x, 0.25)},
        {'name': 'Crop-50%',   'func': lambda x: AttackSuite.crop(x, 0.50)},
        {'name': 'Scale-50%',  'func': lambda x: AttackSuite.scale(x, 0.50)},
        {'name': 'Scale-150%', 'func': lambda x: AttackSuite.scale(x, 1.50)},
        {'name': 'Blur-σ1',    'func': lambda x: AttackSuite.gaussian_blur(x, 1.0)},
        {'name': 'Blur-σ2',    'func': lambda x: AttackSuite.gaussian_blur(x, 2.0)},
        {'name': 'Rotate-5°',  'func': lambda x: AttackSuite.rotation(x, 5)},
        {'name': 'Noise-σ10',  'func': lambda x: AttackSuite.gaussian_noise(x, 10)},
        {'name': 'Combined',   'func': AttackSuite.combined_attack},
    ]


def run_attack_evaluation(watermarker, test_images, test_ids,
                          attack_configs=None, verbose=True):
    """
    Run all attacks and compute metrics.

    Parameters
    ----------
    watermarker : OmniLockWatermarker
    test_images : list of np.ndarray
        Test images, each shape (H, W, 3).
    test_ids : list of np.ndarray
        Corresponding 64-bit watermark IDs.
    attack_configs : list of dict or None
        Custom attack configs; uses standard set if None.
    verbose : bool
        Print results as they are computed.

    Returns
    -------
    summary : pd.DataFrame
        Aggregated metrics per attack type.
    """
    if attack_configs is None:
        attack_configs = get_attack_configs()

    results = []

    for img_idx, (img, true_id) in enumerate(zip(test_images, test_ids)):
        # Embed watermark
        watermarked = watermarker.embed_single_frame(img, true_id)

        # Quality on clean watermark
        quality = evaluate_quality(img, watermarked)

        for cfg in attack_configs:
            try:
                attacked = cfg['func'](watermarked)
                extracted, confidence = watermarker.extract_single_frame(
                    attacked, use_ldpc=False
                )
                ber = float(np.mean(extracted != true_id))
                correct = (ber == 0.0)
            except Exception as e:
                if verbose:
                    print(f"  Error on {cfg['name']}: {e}")
                extracted = np.zeros(64, dtype=int)
                confidence = 0.0
                ber = 0.5
                correct = False

            results.append({
                'image_idx': img_idx,
                'attack': cfg['name'],
                'BER': ber,
                'correct': correct,
                'confidence': confidence,
                'PSNR_dB': quality['PSNR'],
                'SSIM': quality['SSIM']
            })

    df = pd.DataFrame(results)
    summary = df.groupby('attack').agg({
        'BER': 'mean',
        'correct': 'mean',
        'confidence': 'mean',
        'PSNR_dB': 'mean',
        'SSIM': 'mean'
    }).rename(columns={'correct': 'success_rate'})

    if verbose:
        print("\n" + "=" * 60)
        print("  ATTACK EVALUATION RESULTS")
        print("=" * 60)
        print(summary.to_string(float_format='{:.4f}'.format))
        print("=" * 60)

    return summary
