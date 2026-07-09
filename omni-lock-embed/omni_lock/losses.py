import torch
import torch.nn as nn
import torch.nn.functional as F
import math

def bit_loss(soft_preds, true_bits):
    """
    Binary Cross Entropy loss for bit accuracy.
    soft_preds: (B, N) probabilities in [0, 1]
    true_bits: (B, N) target bits in {0.0, 1.0}
    """
    # Use BCE to penalize bit errors directly
    # Clamping soft_preds to avoid log(0) explicitly or relies on BCELoss internally doing it
    loss_fn = nn.BCELoss()
    return loss_fn(soft_preds, true_bits)

def visibility_loss(orig_img, wm_img, window_size=11):
    """
    Computes 1 - SSIM (Structural Similarity) between original and watermarked images.
    Returns the visual difference penalty for image preservation.
    """
    C = orig_img.size(1)
    
    # Create 1D Gaussian kernel
    sigma = 1.5
    gauss = torch.tensor([math.exp(-(x - window_size//2)**2 / float(2 * sigma**2)) for x in range(window_size)])
    gauss = gauss / gauss.sum()
    
    # 2D Gaussian kernel
    kernel_1d = gauss.unsqueeze(1)
    kernel_2d = kernel_1d @ kernel_1d.t()
    kernel = kernel_2d.expand(C, 1, window_size, window_size).to(orig_img.device)
    
    # SSIM formulation
    mu1 = F.conv2d(orig_img, kernel, padding=window_size//2, groups=C)
    mu2 = F.conv2d(wm_img, kernel, padding=window_size//2, groups=C)
    
    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = F.conv2d(orig_img * orig_img, kernel, padding=window_size//2, groups=C) - mu1_sq
    sigma2_sq = F.conv2d(wm_img * wm_img, kernel, padding=window_size//2, groups=C) - mu2_sq
    sigma12 = F.conv2d(orig_img * wm_img, kernel, padding=window_size//2, groups=C) - mu1_mu2
    
    C1 = (0.01 * 255)**2
    C2 = (0.03 * 255)**2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    # Return 1 - SSIM
    return 1.0 - ssim_map.mean()

def soft_parity_loss(soft_preds, H_matrix):
    """
    Multi-objective loss surrogate for the non-differentiable LDPC decoder.
    Penalizes soft bits that do not satisfy the parity equations:
    H * X = 0 (mod 2)
    
    soft_preds: (B, N) soft probabilities
    H_matrix: (M, N) Binary parity check matrix
    """
    # 1. Convert probabilities to BPSK space [-1, 1]
    bpsk = 1.0 - 2.0 * soft_preds 
    
    # 2. Calculate continuous syndromes via matrix multiplication with H^T.
    # In BPSK space, we sum the bits involved in each parity check equation.
    # If a check has degree (d) and is structurally valid, the sum of BPSK values 
    # will be d, d-4, d-8... Invalid combinations will sum to d-2, d-6...
    syndromes = bpsk @ H_matrix.t()
    
    # 3. Penalize bits that do not satisfy the modulo equations.
    # The degree of each parity check is the sum of the rows in the H matrix.
    degrees = H_matrix.sum(dim=1).unsqueeze(0) # (1, M)
    
    # The term (degrees - syndromes) will always be a multiple of 2 in BPSK logic.
    # It is 0, 4, 8... for valid combinations (even number of -1s).
    # It is 2, 6, 10... for invalid combinations (odd number of -1s).
    # Since cos(pi/2 * x) is 1 for {0, 4, 8} and -1 for {2, 6, 10},
    # we can use it to build a flawless continuous differentiable penalty!
    penalty = 1.0 - torch.cos(math.pi / 2.0 * (degrees - syndromes))
    
    return penalty.mean()
