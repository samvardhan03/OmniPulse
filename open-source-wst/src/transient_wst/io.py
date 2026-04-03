"""
transient_wst.io
================
File I/O utilities for loading and saving time-series data stored as
``.npy`` arrays — the canonical interchange format between the MCP
server and the agentic orchestrator.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)


def load_npy_directory(
    directory: str | Path,
    *,
    expected_ndim: int = 2,
) -> list[tuple[str, npt.NDArray[np.float32]]]:
    """Load every ``.npy`` file from *directory*.

    Parameters
    ----------
    directory:
        Path to a folder containing ``.npy`` files.
    expected_ndim:
        Required number of dimensions for each array.  Arrays that do
        not match are skipped with a warning.

    Returns
    -------
    list[tuple[str, ndarray]]
        ``(filename, array)`` pairs, each cast to ``float32``.

    Raises
    ------
    FileNotFoundError
        If *directory* does not exist.
    ValueError
        If no valid ``.npy`` files are found.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    results: list[tuple[str, npt.NDArray[np.float32]]] = []

    for npy_path in sorted(directory.glob("*.npy")):
        arr = np.load(npy_path)

        if arr.ndim != expected_ndim:
            logger.warning(
                "Skipping %s: expected %dD array, got %dD",
                npy_path.name,
                expected_ndim,
                arr.ndim,
            )
            continue

        results.append((npy_path.name, arr.astype(np.float32)))
        logger.debug("Loaded %s — shape %s", npy_path.name, arr.shape)

    if not results:
        raise ValueError(
            f"No valid {expected_ndim}D .npy files found in {directory}"
        )

    logger.info("Loaded %d arrays from %s", len(results), directory)
    return results


def save_arrays(
    arrays: dict[str, npt.NDArray[np.float32]],
    output_dir: str | Path,
) -> list[str]:
    """Save a mapping of ``{name: array}`` into *output_dir* as ``.npy`` files.

    Parameters
    ----------
    arrays:
        Name → array mapping.  Names should NOT include the ``.npy``
        extension; it is appended automatically.
    output_dir:
        Destination directory (created if it does not exist).

    Returns
    -------
    list[str]
        Absolute paths of all saved files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for name, arr in arrays.items():
        stem = name.removesuffix(".npy")
        dest = output_dir / f"{stem}.npy"
        np.save(dest, arr)
        saved.append(str(dest.resolve()))
        logger.debug("Saved %s — shape %s", dest, arr.shape)

    logger.info("Saved %d arrays to %s", len(saved), output_dir)
    return saved
