"""
LDPC Error Correction with Soft-Decision Decoding

Adds redundancy to the watermark so errors introduced by attacks
can be corrected. Uses rate ~0.5 LDPC codes via pyldpc:
  64 information bits → padded to k → 128 coded bits

Key feature: Accepts soft decisions (probabilities) from the extractor
instead of hard bits, enabling much stronger error correction via
belief propagation decoding.

Includes temperature calibration to ensure the extractor's confidence
scores are well-calibrated before feeding to the LDPC decoder.
"""


import numpy as np
import pyldpc

class TemperatureScaling:
    """
    Calibrates soft decisions (probabilities) using temperature scaling.
    This helps the LDPC decoder trust the inputs correctly after 
    watermark extraction noise.
    """
    def __init__(self):
        self.temperature = 1.0

    def fit(self, soft_decisions, true_bits):
        """
        Finds the optimal temperature to minimize cross-entropy.
        For simplicity in this implementation, we use a grid search or 
        heuristic, though a full optimizer (like scipy.optimize) is standard.
        """
        # Ensure inputs are flat for processing
        y_true = true_bits.flatten()
        y_soft = soft_decisions.flatten()
        
        # Avoid log(0)
        y_soft = np.clip(y_soft, 1e-7, 1 - 1e-7)
        
        # Heuristic: Search for temperature that balances the distribution
        # In a real deep learning pipeline, this is learned via SGD.
        best_temp = 1.0
        min_error = float('inf')
        
        for t in np.logspace(-1, 1, 20):
            calibrated = self._apply_temp(y_soft, t)
            error = np.mean((calibrated - y_true)**2)
            if error < min_error:
                min_error = error
                best_temp = t
        
        self.temperature = best_temp

    def _apply_temp(self, x, t):
        # Convert prob to logits, scale, convert back to prob (sigmoid)
        logits = np.log(x / (1 - x))
        return 1.0 / (1.0 + np.exp(-logits / t))

    def calibrate(self, soft_decisions):
        """Applies learned temperature to new soft decisions."""
        return self._apply_temp(soft_decisions, self.temperature)


def create_ldpc_code(n=128, d_v=2, d_c=4):
    """
    Generates LDPC parity check and generator matrices.
    
    Returns
    -------
    H : np.ndarray - Parity check matrix
    G : np.ndarray - Generator matrix
    k : int - Number of message bits (info bits)
    """
    # pyldpc.make_ldpc creates a regular LDPC code
    H, G = pyldpc.make_ldpc(n, d_v, d_c, systematic=True, sparse=False)
    k = G.shape[1] # Number of information bits
    return H, G, k


def ldpc_encode(message, G, k):
    """
    Encodes message bits into a BPSK-modulated codeword.
    
    Parameters
    ----------
    message : np.ndarray - Bits (0 or 1) of length k
    G : np.ndarray - Generator matrix
    k : int - Required length of message
    
    Returns
    -------
    codeword_bpsk : np.ndarray - Codeword in {-1, 1}
    padded_message : np.ndarray - The message used (padded if necessary)
    """
    # Ensure message is correct length or pad it
    padded = np.zeros(k, dtype=int)
    msg_len = min(len(message), k)
    padded[:msg_len] = message[:msg_len]
    
    # pyldpc.encode returns BPSK-modulated codeword (values ≈ ±1)
    # Using high SNR to get essentially noiseless encoding
    codeword_bpsk = pyldpc.encode(G, padded, snr=10000).astype(np.float32)
    
    return codeword_bpsk, padded


def ldpc_decode_soft(soft_decisions, H, G=None, n_message_bits=None,
                     max_iter=100, snr_estimate=5.0):
    """
    Decodes using soft decisions (probabilities).
    
    Parameters
    ----------
    soft_decisions : np.ndarray - Probabilities of bits being '1' [0, 1]
    H : np.ndarray - Parity check matrix
    G : np.ndarray, optional - Generator matrix (needed to extract message bits)
    n_message_bits : int, optional - Original message length to trim output to
    
    Returns
    -------
    decoded_bits : np.ndarray - Hard decisions {0, 1}
    success : bool - Whether the parity check Hx = 0 was satisfied
    """
    # pyldpc.decode expects noisy BPSK signals.
    # Convert probabilities to log-likelihood ratios (LLRs):
    # prob 0.95 -> bit 1 -> value -1.0 (BPSK)
    # prob 0.05 -> bit 0 -> value +1.0 (BPSK)
    y = np.log((1 - soft_decisions) / (soft_decisions + 1e-9))
    
    # Perform Belief Propagation decoding
    decoded_codeword = pyldpc.decode(H, y, snr_estimate, maxiter=max_iter)
    
    # Check if parity bits are satisfied
    success = (np.sum((H @ decoded_codeword) % 2) == 0)
    
    # Extract original message bits from the codeword using G
    if G is not None:
        decoded_message = pyldpc.get_message(G, decoded_codeword)
    else:
        decoded_message = decoded_codeword
    
    # Trim to original message length if specified
    if n_message_bits is not None:
        decoded_message = decoded_message[:n_message_bits]
    
    return decoded_message.astype(int), success