"""
benchmark.py — End-to-end pilot benchmark: Geant4 → r₂ → DisCo / anomaly.

Pipeline
--------
  1. ingest   : load_events() → per-event OIDs in POSIX shm
  2. features : compute r₂ via vikshep.scattering (CUDA) or CPU proxy fallback
  3. disco    : train DisCo classifier for λ ∈ [0, 0.1, 1, 10]
  4. anomaly  : build HNSW index from background r₂; query signal → anomaly scores
  5. metrics  : report Δσ (Asimov significance) and ΔJSD (mass decorrelation)

No tensor array ever travels outside this Python process; only 28-hex OIDs are
passed between the ingest layer and the downstream feature layer.

Gate J validation
-----------------
    python benchmark.py --n-events 400 --seed 42

Expected output (numbers vary with seed):
    Δσ  = <float>  (significance gain from DisCo vs baseline, in σ)
    ΔJSD = <float>  (JSD reduction from DisCo decorrelation)
"""

from __future__ import annotations

import argparse
import sys
import numpy as np
from scipy.spatial.distance import jensenshannon

# ── local pilot imports ─────────────────────────────────────────────────────
_PILOT_DIR = __file__.rsplit("/", 1)[0]
if _PILOT_DIR not in sys.path:
    sys.path.insert(0, _PILOT_DIR)

from load_geant4  import load_events
from train_disco  import extract_r2, extract_baseline_features, sweep_lambda, train_disco


# ---------------------------------------------------------------------------
# Anomaly detection — CPU HNSW via sklearn NearestNeighbors (no MCP required)
#
# Demonstrates the bsm-anomaly recipe:
#   ingest → r₂ OID → feature_oid → HNSW query → {is_anomaly, distance}
# On EDDIE the same logic runs through omnipulse-mcp detect_anomaly tool;
# here we replicate the distance computation in Python for gate validation.
# ---------------------------------------------------------------------------

def _run_anomaly(
    bkg_features: np.ndarray,
    query_features: np.ndarray,
    tau: float | None = None,
    k: int = 10,
) -> dict:
    """
    Build an HNSW-style index from background features and query with test events.

    Returns dict with keys: scores (L2 distances), tau, n_anomalies, recall_at_tau.
    """
    from sklearn.neighbors import NearestNeighbors

    index = NearestNeighbors(n_neighbors=k, algorithm="ball_tree").fit(
        bkg_features.reshape(-1, 1))
    dist, _ = index.kneighbors(query_features.reshape(-1, 1))
    scores  = dist[:, 0]                          # nearest-neighbor L2 distance

    if tau is None:
        tau = float(np.percentile(scores[: len(bkg_features) // 2], 95))

    n_anomalies = int((scores > tau).sum())
    return {
        "scores":        scores,
        "tau":           tau,
        "n_anomalies":   n_anomalies,
    }


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _delta_sigma(
    y_score: np.ndarray,
    y_true:  np.ndarray,
    threshold: float = 0.5,
) -> float:
    """
    Asimov significance Δσ = S / sqrt(B) after applying a score cut.

    S = true-signal events above threshold
    B = background events above threshold
    """
    mask = y_score > threshold
    S = float((y_true[mask] == 1).sum())
    B = float((y_true[mask] == 0).sum()) + 1.0   # +1 to avoid div/0
    return S / np.sqrt(B)


def _jsd(masses_a: np.ndarray, masses_b: np.ndarray, n_bins: int = 30) -> float:
    """Jensen-Shannon divergence between two mass distributions."""
    lo  = min(masses_a.min(), masses_b.min())
    hi  = max(masses_a.max(), masses_b.max())
    bins = np.linspace(lo, hi, n_bins + 1)
    ha, _ = np.histogram(masses_a, bins=bins, density=True)
    hb, _ = np.histogram(masses_b, bins=bins, density=True)
    ha = ha + 1e-10
    hb = hb + 1e-10
    ha /= ha.sum()
    hb /= hb.sum()
    return float(jensenshannon(ha, hb))


def _delta_jsd(
    masses_bkg:        np.ndarray,
    scores_nodisco:    np.ndarray,
    scores_disco:      np.ndarray,
    threshold:         float = 0.5,
) -> float:
    """
    Reduction in JSD(mass | cut) achieved by DisCo decorrelation.

    ΔJSD = JSD_baseline - JSD_disco
    Positive means DisCo distorts the mass spectrum less than the baseline.
    """
    keep_no   = scores_nodisco > threshold
    keep_disco = scores_disco  > threshold

    # Need at least 2 events in both windows
    if keep_no.sum() < 2 or keep_disco.sum() < 2:
        return float("nan")

    jsd_no    = _jsd(masses_bkg, masses_bkg[keep_no])
    jsd_disco = _jsd(masses_bkg, masses_bkg[keep_disco])
    return jsd_no - jsd_disco


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def run_benchmark(
    n_events:         int   = 400,
    seed:             int   = 42,
    signal_fraction:  float = 0.25,
    disco_lambda:     float = 5.0,
    tau_percentile:   float = 90.0,
    root_file:        str | None = None,
) -> dict:
    print(f"[benchmark] Generating {n_events} events (seed={seed})…")
    events  = load_events(root_file, n_events=n_events,
                          signal_fraction=signal_fraction,
                          seed=seed, write_shm=True)

    labels  = np.array([e["is_signal"] for e in events], dtype=np.float32)
    masses  = np.array([e["mass"]      for e in events], dtype=np.float32)
    weights = np.ones(len(events), dtype=np.float32)

    is_bkg = labels == 0
    is_sig = labels == 1

    # ── 1. Feature extraction ────────────────────────────────────────────────
    print("[benchmark] Extracting r₂ features…")
    r2 = extract_r2(events)                         # CUDA if available; else CPU proxy

    print("[benchmark] Extracting 8-feature baseline…")
    X8 = extract_baseline_features(events)

    # ── 2. DisCo training ────────────────────────────────────────────────────
    print("[benchmark] Training DisCo classifier (r₂, λ={:.1f})…".format(disco_lambda))
    res_disco    = train_disco(r2[:, None], labels, masses, weights, lam=disco_lambda)
    scores_disco = res_disco["predict"](r2[:, None]).astype(np.float32)

    print("[benchmark] Training baseline classifier (8 features, no DisCo)…")
    res_base     = train_disco(X8, labels, masses, weights, lam=0.0)
    scores_base  = res_base["predict"](X8).astype(np.float32)

    # ── 3. Anomaly detection — bsm-anomaly recipe ────────────────────────────
    print("[benchmark] Running anomaly detection (bsm-anomaly recipe)…")
    bkg_r2  = r2[is_bkg]
    test_r2 = r2[is_sig]
    tau     = float(np.percentile(bkg_r2, tau_percentile))
    anomaly = _run_anomaly(bkg_r2, test_r2, tau=tau)

    sig_recall = float((anomaly["scores"] > anomaly["tau"]).mean()) if len(test_r2) > 0 else 0.0

    # ── 4. Metrics ────────────────────────────────────────────────────────────
    threshold = 0.5
    ds_base   = _delta_sigma(scores_base,  labels, threshold)
    ds_disco  = _delta_sigma(scores_disco, labels, threshold)
    delta_sig = ds_disco - ds_base

    bkg_masses = masses[is_bkg]
    djsd = _delta_jsd(bkg_masses, scores_base[is_bkg], scores_disco[is_bkg], threshold)

    result = {
        "n_events":         n_events,
        "n_signal":         int(is_sig.sum()),
        "n_background":     int(is_bkg.sum()),
        "auc_baseline":     res_base["auc"],
        "auc_disco":        res_disco["auc"],
        "dcorr2_disco":     res_disco["dcorr2_final"],
        "delta_sigma":      delta_sig,
        "delta_jsd":        djsd,
        "anomaly_tau":      anomaly["tau"],
        "anomaly_recall":   sig_recall,
        "n_anomalies":      anomaly["n_anomalies"],
    }
    return result


def print_report(r: dict) -> None:
    print()
    print("=" * 56)
    print("  OmniPulse Pilot Benchmark — Geant4 calorimeter jets")
    print("=" * 56)
    print(f"  Events      : {r['n_events']}  "
          f"(sig={r['n_signal']}, bkg={r['n_background']})")
    print(f"  AUC baseline: {r['auc_baseline']:.4f}")
    print(f"  AUC DisCo   : {r['auc_disco']:.4f}")
    print(f"  dCorr²(DisCo): {r['dcorr2_disco']:.4f}")
    print("-" * 56)
    print(f"  Δσ  = {r['delta_sigma']:+.4f}  (significance gain vs baseline, σ)")
    print(f"  ΔJSD = {r['delta_jsd']:+.4f}  (mass-shape distortion reduction)")
    print("-" * 56)
    print(f"  Anomaly τ   : {r['anomaly_tau']:.4f}")
    print(f"  Signal recall above τ: {r['anomaly_recall']:.2%}")
    print(f"  Flagged anomalies    : {r['n_anomalies']}")
    print("=" * 56)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniPulse pilot benchmark")
    parser.add_argument("--n-events",        type=int,   default=400)
    parser.add_argument("--seed",            type=int,   default=42)
    parser.add_argument("--signal-fraction", type=float, default=0.25)
    parser.add_argument("--lambda",          type=float, default=5.0, dest="lam")
    parser.add_argument("--tau-percentile",  type=float, default=90.0)
    parser.add_argument("--root-file",       default=None)
    args = parser.parse_args()

    result = run_benchmark(
        n_events        = args.n_events,
        seed            = args.seed,
        signal_fraction = args.signal_fraction,
        disco_lambda    = args.lam,
        tau_percentile  = args.tau_percentile,
        root_file       = args.root_file,
    )
    print_report(result)
