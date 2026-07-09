"""
SpyNetLite — Lightweight coarse-to-fine optical flow estimator.

3-level Gaussian pyramid; 5-layer CNN per level.
Trained from scratch jointly with DifferentiableHEVCSimulator.
No pretrained weights; no .detach() / .numpy() / .round() on the flow path.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


def bilinear_warp(image: Tensor, flow: Tensor) -> Tensor:
    """
    Differentiable bilinear backward warp via grid_sample.

    Parameters
    ----------
    image : (B, C, H, W)  source image to warp
    flow  : (B, 2, H, W)  per-pixel displacement in *pixels* [flow_x, flow_y]

    Returns
    -------
    warped : (B, C, H, W)

    Notes
    -----
    grid_sample flags:
      mode='bilinear'       — bilinear interpolation, correct grad w.r.t. flow
      padding_mode='border' — out-of-boundary pixels clamp to nearest border
      align_corners=True    — corners of the pixel grid are at exactly ±1

    Flow normalization uses (dim-1)/2 (NOT dim/2).  Off-by-one here silently
    kills sub-pixel accuracy because align_corners=True places pixel 0 at -1
    and pixel (dim-1) at +1.
    """
    B, C, H, W = image.shape

    # Base sampling grid in [-1, 1]; ij indexing → first output is H-axis, second is W-axis
    grid_y, grid_x = torch.meshgrid(
        torch.linspace(-1.0, 1.0, H, device=image.device, dtype=image.dtype),
        torch.linspace(-1.0, 1.0, W, device=image.device, dtype=image.dtype),
        indexing='ij',
    )
    # grid_sample expects (B, H, W, 2) with the last dim ordered (x, y)
    base_grid = torch.stack([grid_x, grid_y], dim=-1).unsqueeze(0)  # (1, H, W, 2)

    # Normalize pixel displacement to [-1, 1] using (dim-1)/2
    norm_x = flow[:, 0:1] / ((W - 1) / 2.0)  # (B, 1, H, W)
    norm_y = flow[:, 1:2] / ((H - 1) / 2.0)  # (B, 1, H, W)
    norm_flow = torch.cat([norm_x, norm_y], dim=1).permute(0, 2, 3, 1)  # (B, H, W, 2)

    sample_grid = base_grid + norm_flow  # (B, H, W, 2)

    return F.grid_sample(
        image, sample_grid,
        mode='bilinear',
        padding_mode='border',
        align_corners=True,
    )


class SpyNetLite(nn.Module):
    """
    Lightweight SpyNet-style optical flow estimator.

    Architecture
    ------------
    - `num_levels` coarse-to-fine pyramid levels (default 3)
    - 5-layer CNN per level; kernel size 7×7 throughout
    - Input to each level: warped-prev (C ch) + curr (C ch) + flow (2 ch) = C*2+2 ch
    - Output: per-pixel flow residual (2 ch)

    All operations are fully differentiable.  The flow tensor never touches
    .detach(), .long(), .round(), .floor(), .numpy(), or .item().
    """

    def __init__(self, num_levels: int = 3, base_channels: int = 16):
        super().__init__()
        self.num_levels = num_levels

        # 5-layer CNN per level; input always 8 ch (3+3+2) regardless of image channels
        self.level_cnns = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(8, base_channels, kernel_size=7, padding=3),
                nn.ReLU(inplace=True),
                nn.Conv2d(base_channels, base_channels, kernel_size=7, padding=3),
                nn.ReLU(inplace=True),
                nn.Conv2d(base_channels, base_channels, kernel_size=7, padding=3),
                nn.ReLU(inplace=True),
                nn.Conv2d(base_channels, base_channels, kernel_size=7, padding=3),
                nn.ReLU(inplace=True),
                nn.Conv2d(base_channels, 2, kernel_size=7, padding=3),
            )
            for _ in range(num_levels)
        ])

    def forward(self, prev: Tensor, curr: Tensor) -> Tensor:
        """
        Estimate dense optical flow from prev to curr.

        Parameters
        ----------
        prev, curr : (B, 3, H, W)  frames in [0, 255]

        Returns
        -------
        flow : (B, 2, H, W)  float32, gradient-attached, units = pixels
        """
        # Build Gaussian pyramid; index 0 = finest, index -1 = coarsest
        prev_pyr: list[Tensor] = [prev]
        curr_pyr: list[Tensor] = [curr]
        for _ in range(self.num_levels - 1):
            prev_pyr.append(F.avg_pool2d(prev_pyr[-1], kernel_size=2, stride=2))
            curr_pyr.append(F.avg_pool2d(curr_pyr[-1], kernel_size=2, stride=2))

        # Initialize flow with zeros at the coarsest level
        lH, lW = prev_pyr[-1].shape[2:]
        flow = torch.zeros(prev.shape[0], 2, lH, lW,
                           device=prev.device, dtype=prev.dtype)

        # Coarse-to-fine refinement
        for i in range(self.num_levels - 1, -1, -1):
            p = prev_pyr[i]
            c = curr_pyr[i]
            lH, lW = p.shape[2:]

            # Upsample flow from coarser level and scale by 2 (pixel magnitudes double)
            if i < self.num_levels - 1:
                flow = F.interpolate(flow, size=(lH, lW),
                                     mode='bilinear', align_corners=True) * 2.0

            p_warped = bilinear_warp(p, flow)
            net_in = torch.cat([p_warped, c, flow], dim=1)  # (B, 8, H, W)
            delta = self.level_cnns[i](net_in)
            flow = flow + delta

        return flow
