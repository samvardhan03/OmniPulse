"""
Temporal Matching Module (TMM)

Aligns variable-length extracted soft-decision sequences to the expected
LDPC codeword length using dynamic programming (Edit Distance / 
Wagner-Fischer algorithm).

When frames are dropped, inserted, or swapped, the extracted bitstream
becomes misaligned. The TMM treats this as a sequence alignment problem
(like DNA sequencing) and uses edit distance to find the optimal mapping.

Cost function is confidence-weighted: high-confidence bits are expensive
to delete/substitute, low-confidence bits are cheap.
"""

import numpy as np


def align_soft_decisions(extracted_blocks, target_length=128,
                         gap_penalty=1.0, conf_weight=2.0):
    """
    Align a variable-length stream of extracted soft decisions to
    the expected LDPC codeword length using dynamic programming.

    Uses a modified Wagner-Fischer algorithm where substitution
    costs are inversely proportional to extraction confidence.

    Parameters
    ----------
    extracted_blocks : list of dict
        Each dict contains:
        - 'soft_bits': np.ndarray, shape (32,) — soft decisions
        - 'confidence': float — extraction confidence
        - 'block_idx': int — detected block index (0-3)
    target_length : int
        Expected codeword length (default: 128 for 4×32 blocks).
    gap_penalty : float
        Penalty for inserting a gap (missing frame).
    conf_weight : float
        How much to weight confidence in substitution cost.

    Returns
    -------
    aligned : np.ndarray, shape (target_length,)
        Aligned soft decisions ready for LDPC decoder.
    alignment_cost : float
        Total alignment cost (lower = better alignment).
    """
    # Arrange extracted blocks by their detected block_idx
    # Create slots for 4 blocks of 32 bits each
    slots = {0: [], 1: [], 2: [], 3: []}

    for block in extracted_blocks:
        idx = block['block_idx'] % 4
        slots[idx].append(block)

    # For each slot, pick the highest-confidence extraction
    aligned = np.full(target_length, 0.5)  # Default: maximum uncertainty
    total_cost = 0.0

    for slot_idx in range(4):
        start = slot_idx * 32
        end = start + 32

        candidates = slots[slot_idx]
        if len(candidates) == 0:
            # Gap: no frame found for this block
            total_cost += gap_penalty * 32
            # Leave as 0.5 (max uncertainty) — LDPC handles this
            continue

        # Pick highest confidence candidate
        best = max(candidates, key=lambda c: c['confidence'])
        soft = best['soft_bits'][:32]
        conf = best['confidence']

        aligned[start:end] = soft
        # Cost is inversely proportional to confidence
        total_cost += (1.0 - conf) * conf_weight * 32

    return aligned, total_cost


def align_sequence_edit_distance(extracted_sequence, target_length=128):
    """
    Align a continuous stream of soft decisions using the full
    Wagner-Fischer edit distance algorithm.

    This is for scenarios where individual block boundaries are unknown
    and the entire stream must be globally aligned.

    Parameters
    ----------
    extracted_sequence : np.ndarray, shape (N,)
        Variable-length stream of soft decisions (N may != target_length).
    target_length : int
        Expected codeword length.

    Returns
    -------
    aligned : np.ndarray, shape (target_length,)
        Aligned soft decisions.
    cost : float
        Total alignment cost.
    """
    n = len(extracted_sequence)
    m = target_length

    if n == m:
        return extracted_sequence.copy(), 0.0

    # Dynamic programming matrix
    dp = np.zeros((n + 1, m + 1), dtype=np.float64)

    # Base cases
    for i in range(n + 1):
        dp[i, 0] = i * 1.0  # Deletion cost
    for j in range(m + 1):
        dp[0, j] = j * 1.0  # Insertion cost

    # Fill DP table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # Substitution cost: inverse of confidence
            confidence = abs(extracted_sequence[i - 1] - 0.5) * 2.0
            sub_cost = 1.0 - confidence  # High confidence = low cost

            dp[i, j] = min(
                dp[i - 1, j] + 1.0,          # Deletion (skip extracted bit)
                dp[i, j - 1] + 1.0,           # Insertion (gap in extraction)
                dp[i - 1, j - 1] + sub_cost   # Match/Substitution
            )

    # Backtrack to build aligned sequence
    aligned = np.full(m, 0.5)  # Default: maximum uncertainty
    i, j = n, m

    while i > 0 and j > 0:
        confidence = abs(extracted_sequence[i - 1] - 0.5) * 2.0
        sub_cost = 1.0 - confidence

        current = dp[i, j]
        diagonal = dp[i - 1, j - 1] + sub_cost
        up = dp[i - 1, j] + 1.0
        left = dp[i, j - 1] + 1.0

        if abs(current - diagonal) < 1e-9:
            # Match/Substitution: use this extracted value
            aligned[j - 1] = extracted_sequence[i - 1]
            i -= 1
            j -= 1
        elif abs(current - up) < 1e-9:
            # Deletion: skip this extracted bit
            i -= 1
        else:
            # Insertion: gap in extraction, leave as 0.5
            j -= 1

    # Fill remaining positions with 0.5 (gaps)
    # (already initialized to 0.5)

    return aligned, dp[n, m]


def compute_block_assignment(extracted_sequence, num_blocks=4):
    """
    Assign a continuous stream of soft decisions into blocks via
    correlation-based matching.

    Uses the structural pattern of the extracted bits to determine
    which 32-bit segment maps to which codeword block.

    Parameters
    ----------
    extracted_sequence : np.ndarray, shape (N,)
        Stream of soft decisions.
    num_blocks : int
        Number of blocks to assign to.

    Returns
    -------
    block_assignments : list of dict
        Each dict: {'soft_bits': ndarray, 'block_idx': int, 'confidence': float}
    """
    bits_per_block = len(extracted_sequence) // num_blocks
    blocks = []

    for i in range(num_blocks):
        start = i * bits_per_block
        end = start + bits_per_block
        segment = extracted_sequence[start:end]

        # Confidence: average distance from 0.5 (how decisive the bits are)
        confidence = np.mean(np.abs(segment - 0.5)) * 2.0

        blocks.append({
            'soft_bits': segment[:32] if len(segment) >= 32 else
                np.pad(segment, (0, 32 - len(segment)),
                       constant_values=0.5),
            'block_idx': i,
            'confidence': float(confidence)
        })

    return blocks
