"""
load_geant4.py — Geant4 / ROOT calorimeter event loader for the pilot.

When a .root file is provided, delegates to the vikshep-ingest ROOT/uproot loader.
When no file is given, or on hosts without uproot/ROOT, generates synthetic
η×φ calorimeter images that mimic single-prong QCD jets (background) and
two-prong top/W jets (signal).

Return contract
---------------
load_events(path, n_events, signal_fraction, seed)
    -> list[dict]  each dict has:
       "img"        : np.ndarray shape (ETA_BINS, PHI_BINS) float32
       "is_signal"  : bool
       "mass"       : float  (GeV-scale proxy)
       "weight"     : float  (FullEventWeight; 1.0 for synthetic)
       "oid"        : str    (28-hex POSIX shm name written by SharedMemoryManager)
       "signal_len" : int    (== ETA_BINS * PHI_BINS)
       "meta"       : dict   {dim, group, shape, pad}
"""

from __future__ import annotations

import sys
import numpy as np

ETA_BINS: int = 64
PHI_BINS: int = 64

_DEFAULT_META: dict = {
    "dim": 2,
    "group": "so2",
    "shape": [ETA_BINS, PHI_BINS],
    "pad": [{"axis": "zero"}, {"axis": "circular"}],  # η zero-pad, φ circular
}


# ---------------------------------------------------------------------------
# Synthetic jet generator
# ---------------------------------------------------------------------------

def _synthetic_jet(rng: np.random.Generator, is_signal: bool) -> np.ndarray:
    img = rng.exponential(0.3, (ETA_BINS, PHI_BINS)).astype(np.float32)  # soft UE

    eta_c = int(rng.integers(20, ETA_BINS - 20))
    phi_c = int(rng.integers(20, PHI_BINS - 20))

    # Main jet core — narrow Gaussian deposit
    for de in range(-10, 11):
        for dp in range(-10, 11):
            r2 = de * de + dp * dp
            e = float(rng.exponential(12.0 * np.exp(-r2 / 20.0)))
            img[(eta_c + de) % ETA_BINS, (phi_c + dp) % PHI_BINS] += e

    if is_signal:
        # Extra prong displaced by ~(3,3) cells — two-prong substructure
        offset_eta = int(rng.integers(-5, 6))
        offset_phi = int(rng.integers(-5, 6))
        eta_s = eta_c + offset_eta
        phi_s = phi_c + offset_phi
        for de in range(-5, 6):
            for dp in range(-5, 6):
                r2 = de * de + dp * dp
                e = float(rng.exponential(6.0 * np.exp(-r2 / 10.0)))
                img[(eta_s + de) % ETA_BINS, (phi_s + dp) % PHI_BINS] += e

    return img


def _synthetic_mass(rng: np.random.Generator, is_signal: bool) -> float:
    if is_signal:
        return float(abs(rng.normal(172.5, 18.0)))   # top quark proxy ~173 GeV
    else:
        return float(abs(rng.normal(80.0, 14.0)))    # QCD / W bkg proxy


# ---------------------------------------------------------------------------
# Ingest helper — writes image to POSIX shm, returns 28-hex OID
# ---------------------------------------------------------------------------

def _ingest_to_shm(arr: np.ndarray) -> str:
    try:
        from shared_memory_manager import SharedMemoryManager
        return SharedMemoryManager().ingest_media_tensor(arr)
    except Exception as exc:
        print(f"[load_geant4] shm ingest failed ({exc}); OID set to empty", file=sys.stderr)
        return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_events(
    path: str | None = None,
    n_events: int = 500,
    signal_fraction: float = 0.3,
    seed: int = 42,
    write_shm: bool = True,
) -> list[dict]:
    """
    Load or generate calorimeter events.

    Parameters
    ----------
    path            : path to a .root file; if None or load fails → synthetic
    n_events        : number of events to generate (synthetic mode)
    signal_fraction : fraction of signal jets (synthetic mode)
    seed            : RNG seed for reproducibility
    write_shm       : write each image to POSIX shm and record OID

    Returns
    -------
    list of event dicts (see module docstring)
    """
    if path is not None:
        events = _load_root(path, write_shm=write_shm, seed=seed)
        if events:
            return events
        print("[load_geant4] falling back to synthetic data", file=sys.stderr)

    rng = np.random.default_rng(seed)
    events: list[dict] = []

    for i in range(n_events):
        is_signal = bool(rng.random() < signal_fraction)
        img   = _synthetic_jet(rng, is_signal)
        mass  = _synthetic_mass(rng, is_signal)
        arr   = np.ascontiguousarray(img, dtype=np.float32)
        oid   = _ingest_to_shm(arr) if write_shm else ""
        events.append({
            "img":        img,
            "is_signal":  is_signal,
            "mass":       mass,
            "weight":     1.0,
            "oid":        oid,
            "signal_len": int(arr.size),
            "meta":       _DEFAULT_META.copy(),
        })

    return events


def _load_root(path: str, write_shm: bool, seed: int) -> list[dict]:
    try:
        from vikshep_ingest.loaders.root_uproot import RootUprootLoader
        loader = RootUprootLoader()
        arr, meta = loader.load(path)
        rng = np.random.default_rng(seed)
        events = []
        imgs = arr if arr.ndim == 3 else arr[np.newaxis]
        n = len(imgs)
        labels = rng.random(n) < 0.3
        for i, img in enumerate(imgs):
            img32 = np.ascontiguousarray(img, dtype=np.float32)
            oid = _ingest_to_shm(img32) if write_shm else ""
            events.append({
                "img":        img32,
                "is_signal":  bool(labels[i]),
                "mass":       float(abs(rng.normal(80, 15))),
                "weight":     1.0,
                "oid":        oid,
                "signal_len": int(img32.size),
                "meta":       meta.copy(),
            })
        return events
    except Exception as exc:
        print(f"[load_geant4] root loader: {exc}", file=sys.stderr)
        return []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load / generate Geant4 calorimeter events")
    parser.add_argument("--root-file", default=None, help="Path to .root file")
    parser.add_argument("--n-events", type=int, default=100)
    parser.add_argument("--seed",     type=int, default=42)
    parser.add_argument("--no-shm",   action="store_true")
    args = parser.parse_args()

    events = load_events(args.root_file, n_events=args.n_events,
                         seed=args.seed, write_shm=not args.no_shm)
    n_sig = sum(e["is_signal"] for e in events)
    print(f"Loaded {len(events)} events  ({n_sig} signal, {len(events)-n_sig} background)")
    print(f"Sample OID (first event): {events[0]['oid'] or '(shm disabled)'}")
    print(f"Image shape: {events[0]['img'].shape}  dtype: {events[0]['img'].dtype}")
