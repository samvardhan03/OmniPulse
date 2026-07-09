import torch
import torch.nn as nn
import torch.nn.functional as F
import math


def midfreq_mask(block_size: int = 8) -> torch.Tensor:
    """
    Return a float32 (block_size, block_size) mask that is 1.0 where
    2 ≤ u+v ≤ 6 (mid-frequency band) and 0.0 elsewhere.
    This defines B from: M_t = T⁻¹(T(M̃_t) ⊗ B).
    """
    mask = torch.zeros(block_size, block_size)
    for u in range(block_size):
        for v in range(block_size):
            if 2 <= u + v <= 6:
                mask[u, v] = 1.0
    return mask


class DCT2D:
    def __init__(self, block_size=8, device='cpu'):
        self.block_size = block_size
        self.device = device
        self.D = self._get_dct_matrix(block_size).to(device)
        self.D_T = self.D.transpose(0, 1)

    def _get_dct_matrix(self, N):
        """Creates the N x N 1D DCT-II orthonormal basis matrix."""
        D = torch.zeros(N, N)
        for k in range(N):
            for n in range(N):
                if k == 0:
                    val = math.sqrt(1.0 / N)
                else:
                    val = math.sqrt(2.0 / N) * math.cos(math.pi * k * (2 * n + 1) / (2 * N))
                D[k, n] = val
        return D

    def dct2(self, x):
        """
        Batched 2D DCT.
        x shape: (B, N, N)
        Returns: DCT(x) = D * x * D^T
        """
        B_size = x.size(0)
        D_batch = self.D.unsqueeze(0).expand(B_size, -1, -1)
        D_T_batch = self.D_T.unsqueeze(0).expand(B_size, -1, -1)
        return torch.bmm(torch.bmm(D_batch, x), D_T_batch)

    def idct2(self, X):
        """
        Batched 2D IDCT.
        X shape: (B, N, N)
        Returns: IDCT(X) = D^T * X * D
        """
        B_size = X.size(0)
        D_batch = self.D.unsqueeze(0).expand(B_size, -1, -1)
        D_T_batch = self.D_T.unsqueeze(0).expand(B_size, -1, -1)
        return torch.bmm(torch.bmm(D_T_batch, X), D_batch)

def blockify(img, block_size=8):
    """
    Chops an image tensor into blocks.
    img: (B, C, H, W)
    Returns: (B*C*num_blocks, block_size, block_size)
    """
    B, C, H, W = img.shape
    blocks = img.unfold(2, block_size, block_size).unfold(3, block_size, block_size)
    blocks = blocks.contiguous().view(-1, block_size, block_size)
    return blocks

def deblockify(blocks, shape_pad, block_size=8):
    """
    Reconstructs an image from blocks.
    blocks: (B*C*num_blocks, block_size, block_size)
    shape_pad: (B, C, H_pad, W_pad)
    """
    B, C, H_pad, W_pad = shape_pad
    num_blocks_h = H_pad // block_size
    num_blocks_w = W_pad // block_size
    blocks = blocks.view(B, C, num_blocks_h, num_blocks_w, block_size, block_size)
    blocks = blocks.permute(0, 1, 2, 4, 3, 5).contiguous()
    return blocks.view(B, C, H_pad, W_pad)

class DifferentiableDCTEmbedder(nn.Module):
    def __init__(self, block_size=8, alpha=0.1):
        super().__init__()
        self.block_size = block_size
        self.alpha = alpha
        self.freq_mask = midfreq_mask(block_size)

    def forward(self, image, spatial_mask):
        """
        Embed spatial_mask into image mid-freq DCT coefficients.
        image: (B, C, H, W) tensor
        spatial_mask: (B, H, W) tensor
        """
        B, C, H, W = image.shape
        device = image.device
        
        # Apple MPS crashes on 2D F.pad with mode='reflect'. Ensure 4D structure for spatial mask.
        mask_4d = spatial_mask.unsqueeze(1) # (B, 1, H, W)
        
        pad_h = (self.block_size - H % self.block_size) % self.block_size
        pad_w = (self.block_size - W % self.block_size) % self.block_size
        
        if pad_h > 0 or pad_w > 0:
            image_pad = F.pad(image, (0, pad_w, 0, pad_h), mode='reflect')
            mask_pad = F.pad(mask_4d, (0, pad_w, 0, pad_h), mode='reflect')
        else:
            image_pad = image
            mask_pad = mask_4d
            
        shape_pad = image_pad.shape
        
        # Scale mask so DCT coefficients are large enough for alpha logic to work (matching numpy code)
        mask_pad = mask_pad * 50.0
        
        # Broadcast the mask logically across color channels
        mask_pad = mask_pad.expand(-1, C, -1, -1).clone()
        
        img_blocks = blockify(image_pad, self.block_size)
        mask_blocks = blockify(mask_pad, self.block_size)
        
        dct_engine = DCT2D(block_size=self.block_size, device=device)
        
        # Convert to frequency domain
        dct_img = dct_engine.dct2(img_blocks)
        dct_mask = dct_engine.dct2(mask_blocks)
        
        # Apply the update only to mid-frequency band
        freq_mask = self.freq_mask.to(device).unsqueeze(0).expand(dct_img.size(0), -1, -1)
        dct_mod = dct_img + self.alpha * dct_mask * freq_mask
        
        # Inverse transform
        img_mod_blocks = dct_engine.idct2(dct_mod)
        
        # Reconstruct image
        img_mod_pad = deblockify(img_mod_blocks, shape_pad, self.block_size)
        
        # Remove padding
        watermarked = img_mod_pad[:, :, :H, :W]
        
        # Important: clamp the tensor values, preserving float32 differentiability
        watermarked = watermarked.clamp(0.0, 255.0)
        
        return watermarked
