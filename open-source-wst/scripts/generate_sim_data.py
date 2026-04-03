"""
scripts/generate_sim_data.py
----------------------------
Generates synthetic 1-D time-series signals saved as .npy arrays.
Each file mimics 2 seconds of data at 1000 Hz.

Most files contain Gaussian white noise, but specifically:
  - 10 files contain a high-frequency chirp transient.
  - 2 files contain extreme mathematical anomalies (massive flatline, inf spikes).

This validates the Agentic QueryEngine's variance-based outlier
rejection tools.
"""

import os
import argparse
import numpy as np

def generate_signals(output_dir: str, n_files: int = 50) -> None:
    os.makedirs(output_dir, exist_ok=True)
    fs = 1000
    n_samples = 2 * fs # 2 seconds
    t = np.arange(n_samples) / fs

    # Deterministic randomness for repeatability
    rng = np.random.default_rng(42)

    indices = rng.permutation(n_files)
    transient_idx = set(indices[:10])
    anomaly_idx = set(indices[10:12])

    print(f"Generating {n_files} total files in '{output_dir}'")
    print(f"Injecting transients at indices: {sorted(list(transient_idx))}")
    print(f"Injecting anomalies at indices: {sorted(list(anomaly_idx))}")

    transient_count = 0
    anomaly_count = 0

    for i in range(n_files):
        # Base signal: random normal distribution
        signal = rng.standard_normal(n_samples)

        if i in transient_idx:
            # Inject non-stationary transient (high frequency chirp)
            f0, f1 = 50, 200
            start_i, end_i = 600, 1400
            t_chirp = t[start_i:end_i]
            
            # Simple chirp
            chirp = np.sin(2 * np.pi * (f0 + (f1 - f0) * t_chirp / (2 * t_chirp[-1])) * t_chirp)
            window = np.hanning(len(chirp))
            
            # Amplified and injected
            signal[start_i:end_i] += chirp * window * 10.0
            transient_count += 1
            
        elif i in anomaly_idx:
            # Massive artifacts to trigger artifact rejection
            if anomaly_count % 2 == 0:
                # Extreme infinity spikes simulating disconnected electrode
                signal[800:810] = np.inf
                signal[1500:1510] = -np.inf
            else:
                # Flatline with massive DC offset
                signal[500:1800] = 1_000_000.0
            anomaly_count += 1

        # Reshape to 2-D (Batch=1, Time=n_samples) and cast to float32
        # Kymatio expects [B, T] inputs
        final_array = signal.reshape(1, -1).astype(np.float32)
        
        filename = os.path.join(output_dir, f"signal_{i:03d}.npy")
        np.save(filename, final_array)

    print("Data generation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic .npy data")
    parser.add_argument(
        "--output", 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), "..", "data", "raw_sim"),
        help="Output directory to save the arrays"
    )
    args = parser.parse_args()
    generate_signals(args.output)
