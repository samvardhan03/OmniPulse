from __future__ import annotations

__version__ = "0.3.0"

import numpy as np

try:
    from ._scatter import scattering as _scatter_cuda
    _CUDA = True
except ImportError:
    _CUDA = False
    _scatter_cuda = None


def cuda_available() -> bool:
    """Return True if the CUDA extension was compiled and loaded."""
    return _CUDA


def scattering(
    arr: "np.ndarray",
    dim: int,
    group: str,
    J: int,
    Q: int,
    L: int = 1,
    order: int = 2,
) -> "np.ndarray":
    """Compute n-D wavelet scattering coefficients.

    Parameters
    ----------
    arr   : float32 C-contiguous NumPy array
    dim   : signal dimensionality (1, 2, or 3)
    group : symmetry group ('trivial', 'so2', or 'so3')
    J     : number of octaves (1..14)
    Q     : wavelets per octave (1..32)
    L     : angular resolution for SE(2)/SO(3) (1..16, ignored for trivial)
    order : scattering order (1 or 2)

    Returns
    -------
    numpy.ndarray  1-D float32 coefficient array
    """
    if not _CUDA:
        raise RuntimeError(
            "vikshep CUDA extension not built. "
            "On EDDIE: module load cuda/12.4 && pip install -e . --no-build-isolation"
        )
    arr = np.ascontiguousarray(arr, dtype=np.float32)
    return _scatter_cuda(arr, dim, group, J, Q, L, order)


__all__ = ["__version__", "cuda_available", "scattering"]
