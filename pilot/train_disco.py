"""
train_disco.py — DisCo (Distance Correlation) classifier for mass-decorrelated jet tagging.

Loss function
-------------
L_DisCo(θ; λ) = wBCE(ŷ, y; w) + λ · dCorr²_w(ŷ, m | bkg)

  wBCE    : sample-weighted binary cross-entropy
  dCorr   : weighted distance correlation between classifier score ŷ
            and jet mass m, evaluated on background events only
  λ       : decorrelation strength hyperparameter (sweep: [0, 0.1, 1, 10])
  w       : FullEventWeight (all 1.0 for synthetic data; per-event weights for MC)

Feature extraction
------------------
When vikshep.scattering (CUDA) is available:
    r₂ = reduce_scattering(compute_scattering(img, dim=2, group="so2", J=4, L=8), method="ratio")

On non-CUDA hosts:
    A CPU proxy r₂ is computed from the image using multi-scale Gaussian
    energy ratios — same structural interpretation, no GPU required.

Training approach
-----------------
Gradient descent on logistic regression with analytic DisCo penalty gradient.
The dCorr² gradient w.r.t. the classifier output uses the Pearson-correlation
approximation (fast O(N), valid for the pilot sweep).
"""

from __future__ import annotations

import sys
import warnings
import numpy as np
from scipy.ndimage import gaussian_filter

warnings.filterwarnings("ignore", category=UserWarning)


# ---------------------------------------------------------------------------
# CPU feature extraction — r₂ proxy via multi-scale energy ratio
# ---------------------------------------------------------------------------

def _cpu_r2(img: np.ndarray, sigma_fine: float = 1.0, sigma_coarse: float = 4.0) -> float:
    """
    CPU approximation of r₂ = mean(S₂) / mean(S₁).

    Uses a two-scale Gaussian decomposition: fine-scale energy = S₂ proxy,
    coarse-scale energy = S₁ proxy.
    """
    fine   = gaussian_filter(img.astype(np.float64), sigma=sigma_fine)
    coarse = gaussian_filter(img.astype(np.float64), sigma=sigma_coarse)
    detail = np.abs(fine - coarse)
    s2_proxy = np.mean(detail)
    s1_proxy = np.mean(coarse) + 1e-12
    return float(s2_proxy / s1_proxy)


def _cuda_r2(img: np.ndarray) -> float:
    """Use vikshep CUDA engine: compute_scattering(dim=2, group=so2, J=4, L=8) → ratio."""
    import vikshep
    arr    = np.ascontiguousarray(img, dtype=np.float32)
    coeffs = vikshep.scattering(arr, dim=2, group="so2", J=4, Q=1, L=8, order=2)
    half   = len(coeffs) // 2
    s1     = float(np.mean(coeffs[:half])) + 1e-12
    s2     = float(np.mean(coeffs[half:]))
    return s2 / s1


def extract_r2(events: list[dict], cuda: bool | None = None) -> np.ndarray:
    """
    Extract per-event r₂ features.  Returns shape (N,).

    If cuda is None, attempts CUDA first and falls back to CPU.
    """
    if cuda is None:
        try:
            import vikshep as _v
            cuda = _v.cuda_available()
        except ImportError:
            cuda = False

    r2_vals: list[float] = []
    for ev in events:
        if cuda:
            try:
                r2_vals.append(_cuda_r2(ev["img"]))
                continue
            except Exception as exc:
                print(f"[train_disco] CUDA r₂ failed ({exc}); switching to CPU", file=sys.stderr)
                cuda = False
        r2_vals.append(_cpu_r2(ev["img"]))

    return np.array(r2_vals, dtype=np.float32)


# ---------------------------------------------------------------------------
# Baseline 8-feature set (no scattering — comparable to hand-crafted HEP features)
# ---------------------------------------------------------------------------

def extract_baseline_features(events: list[dict]) -> np.ndarray:
    """
    Eight image-level features used as the baseline (no scattering).

    [total_e, eta_mean, phi_mean, eta_std, phi_std, max_e, n_cells_gt0, eccentricity]
    """
    rows: list[list[float]] = []
    eta_idx = np.arange(64, dtype=np.float64)
    phi_idx = np.arange(64, dtype=np.float64)
    for ev in events:
        img     = ev["img"].astype(np.float64)
        total_e = img.sum() + 1e-9
        eta_sum = img.sum(axis=1)
        phi_sum = img.sum(axis=0)
        eta_mean = float((eta_sum @ eta_idx) / total_e)
        phi_mean = float((phi_sum @ phi_idx) / total_e)
        eta_std  = float(np.sqrt((eta_sum @ (eta_idx - eta_mean) ** 2) / total_e))
        phi_std  = float(np.sqrt((phi_sum @ (phi_idx - phi_mean) ** 2) / total_e))
        max_e    = float(img.max())
        n_cells  = float((img > 0).sum())
        ecc      = float((eta_std - phi_std) / (eta_std + phi_std + 1e-9))
        rows.append([total_e, eta_mean, phi_mean, eta_std, phi_std, max_e, n_cells, ecc])
    return np.array(rows, dtype=np.float32)


# ---------------------------------------------------------------------------
# Weighted distance correlation (exact, O(N²), for metrics only)
# ---------------------------------------------------------------------------

def weighted_dcorr2(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    """
    Weighted distance correlation² between 1-D arrays x and y with weights w.
    Székely & Rizzo (2014) formulation with sample weights.
    """
    w   = w / w.sum()
    ax  = np.abs(x[:, None] - x[None, :]).astype(np.float64)
    ay  = np.abs(y[:, None] - y[None, :]).astype(np.float64)
    row_ax = (ax * w[None, :]).sum(axis=1)
    row_ay = (ay * w[None, :]).sum(axis=1)
    mu_ax  = float((row_ax * w).sum())
    mu_ay  = float((row_ay * w).sum())
    A  = ax - row_ax[:, None] - row_ax[None, :] + mu_ax
    B  = ay - row_ay[:, None] - row_ay[None, :] + mu_ay
    W  = w[:, None] * w[None, :]
    dcov2_xy = float((W * A * B).sum())
    dcov2_xx = float((W * A * A).sum())
    dcov2_yy = float((W * B * B).sum())
    denom = np.sqrt(max(dcov2_xx * dcov2_yy, 0.0))
    return float(dcov2_xy / denom) if denom > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# DisCo penalty gradient — Pearson approximation (fast, O(N))
# ---------------------------------------------------------------------------

def _pearson_dcorr2_grad(
    scores: np.ndarray,
    masses: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    """
    Analytic gradient of Pearson r²(scores, masses) w.r.t. scores.

    Used as a fast O(N) proxy for the dCorr² gradient during training.
    The Pearson correlation understates the true distance correlation for
    nonlinear dependence, but it is sufficient to drive decorrelation in
    the pilot sweep.
    """
    w  = weights / weights.sum()
    mu_s = float((scores * w).sum())
    mu_m = float((masses * w).sum())
    ds = scores - mu_s
    dm = masses - mu_m
    cov    = float((ds * dm * w).sum())
    var_s  = float((ds ** 2 * w).sum()) + 1e-12
    var_m  = float((dm ** 2 * w).sum()) + 1e-12
    r      = cov / np.sqrt(var_s * var_m)
    # ∂r²/∂s_i = 2r · w_i · [dm_i / sqrt(var_s*var_m) - r*ds_i/var_s]
    grad_r2 = 2.0 * r * w * (dm / np.sqrt(var_s * var_m) - r * ds / var_s)
    return grad_r2.astype(np.float64)


# ---------------------------------------------------------------------------
# DisCo logistic regression trainer
# ---------------------------------------------------------------------------

def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def train_disco(
    features: np.ndarray,
    labels:   np.ndarray,
    masses:   np.ndarray,
    weights:  np.ndarray | None = None,
    lam:      float = 1.0,
    lr:       float = 0.05,
    n_iter:   int   = 400,
) -> dict:
    """
    Train a DisCo logistic regression classifier.

    Parameters
    ----------
    features : (N, d) float32 feature matrix
    labels   : (N,) binary labels (1 = signal, 0 = background)
    masses   : (N,) jet mass proxy
    weights  : (N,) event weights; defaults to uniform
    lam      : DisCo decorrelation strength
    lr       : gradient descent learning rate
    n_iter   : gradient descent steps

    Returns
    -------
    dict with keys: theta, auc, disco_loss_final, dcorr2_final, predict
    """
    N, d = features.shape
    if weights is None:
        weights = np.ones(N, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    X = np.ascontiguousarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    m = np.asarray(masses, dtype=np.float64)

    mu   = X.mean(axis=0, keepdims=True)
    std  = X.std(axis=0, keepdims=True) + 1e-8
    X    = (X - mu) / std
    m_n  = (m - m.mean()) / (m.std() + 1e-8)    # normalised mass for stable gradient

    theta = np.zeros(d + 1, dtype=np.float64)    # [bias, w₁, …, wₐ]
    bkg   = y == 0

    def forward(X_: np.ndarray) -> np.ndarray:
        return _sigmoid(X_ @ theta[1:] + theta[0])

    w_norm = w / w.sum()

    for _ in range(n_iter):
        p    = forward(X)
        err  = p - y

        # BCE gradient
        grad = np.zeros(d + 1, dtype=np.float64)
        grad[0]  = (err * w_norm).sum()
        grad[1:] = (X * (err * w_norm)[:, None]).sum(axis=0)

        # DisCo penalty gradient (Pearson proxy, background only)
        if lam > 0.0 and bkg.sum() >= 4:
            p_bkg   = p[bkg]
            m_bkg   = m_n[bkg]
            w_bkg   = w[bkg]
            dg_bkg  = _pearson_dcorr2_grad(p_bkg, m_bkg, w_bkg)
            # ∂L/∂θ = λ · ∂r²/∂p · ∂p/∂θ = λ · dg · p(1-p) · x
            dg_full = np.zeros(N, dtype=np.float64)
            dg_full[bkg] = dg_bkg * p_bkg * (1.0 - p_bkg)
            grad[0]  += lam * (dg_full * w_norm).sum()
            grad[1:] += lam * (X * (dg_full * w_norm)[:, None]).sum(axis=0)

        theta -= lr * grad

    # Final metrics
    p_final = forward(X)
    eps     = 1e-7
    p_c     = np.clip(p_final, eps, 1 - eps)
    bce     = float(-((y * np.log(p_c) + (1 - y) * np.log(1 - p_c)) * w_norm).sum())

    dc2_final = 0.0
    if bkg.sum() >= 4:
        dc2_final = weighted_dcorr2(p_final[bkg], m[bkg], w[bkg])

    from sklearn.metrics import roc_auc_score
    try:
        auc = float(roc_auc_score(y.astype(int), p_final))
    except Exception:
        auc = float("nan")

    return {
        "theta":            theta,
        "mu":               mu,
        "std":              std,
        "auc":              auc,
        "bce_final":        bce,
        "dcorr2_final":     dc2_final,
        "disco_loss_final": bce + lam * dc2_final,
        "predict":          lambda X_new: _sigmoid(
            ((np.ascontiguousarray(X_new, dtype=np.float64) - mu) / std)
            @ theta[1:] + theta[0]
        ).astype(np.float32),
    }


def sweep_lambda(
    features: np.ndarray,
    labels:   np.ndarray,
    masses:   np.ndarray,
    weights:  np.ndarray | None = None,
    lambdas:  list[float] | None = None,
) -> list[dict]:
    """Train DisCo for each λ and return results sorted by λ."""
    if lambdas is None:
        lambdas = [0.0, 0.1, 1.0, 10.0]
    results = []
    for lam in lambdas:
        r = train_disco(features, labels, masses, weights, lam=lam)
        r["lambda"] = lam
        results.append(r)
    return results


if __name__ == "__main__":
    import argparse
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from load_geant4 import load_events

    parser = argparse.ArgumentParser()
    parser.add_argument("--n-events", type=int, default=300)
    parser.add_argument("--seed",     type=int, default=42)
    args = parser.parse_args()

    print("Generating events…")
    events  = load_events(n_events=args.n_events, seed=args.seed, write_shm=False)
    labels  = np.array([e["is_signal"] for e in events], dtype=np.float32)
    masses  = np.array([e["mass"]      for e in events], dtype=np.float32)
    weights = np.ones(len(events), dtype=np.float32)

    print("Extracting r₂ features (CPU)…")
    r2 = extract_r2(events, cuda=False)
    X  = r2[:, None]

    print("Sweeping λ…")
    for res in sweep_lambda(X, labels, masses, weights):
        print(f"  λ={res['lambda']:5.1f}  AUC={res['auc']:.4f}  "
              f"dCorr²={res['dcorr2_final']:.4f}  BCE={res['bce_final']:.4f}")
