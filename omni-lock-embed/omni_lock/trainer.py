import torch
import torchvision.transforms as T
import torch.nn.functional as F

class WatermarkTrainer:
    """
    3-Phase Curriculum Trainer for End-to-End Differentiable Watermarking.
    """
    def __init__(self, mixer_subnet, dct_embedder, extractor_subnet, H_matrix, 
                 lr=1e-3, device='cpu'):
        self.device = device
        self.mixer = mixer_subnet.to(device)
        self.embedder = dct_embedder.to(device)
        self.extractor = extractor_subnet.to(device)
        self.H_matrix = H_matrix.float().to(device)
        
        # 3-Phase Curriculum state
        self.phase = 1
        self.phase2_steps = 0  # To track steps after Phase 1 for dynamic weighting
        
        # Optimizer
        self.optimizer = torch.optim.Adam(
            list(self.mixer.parameters()) + list(self.extractor.parameters()), 
            lr=lr
        )
        
        # Differentiable Attacks
        self.blur_transform = T.GaussianBlur(kernel_size=(5, 9), sigma=(0.1, 2.0))
        
    def apply_differentiable_attacks(self, images):
        """
        Applies differentiable Additive Noise, Gaussian Blur, and Spatial Crop
        to simulate real-world compression and edits natively on MPS/GPU.
        """
        B, C, H, W = images.shape
        
        # 1. Additive Noise (surrogate for JPEG quantization & sensor noise)
        noise = torch.randn_like(images) * 5.0
        attacked = (images + noise).clamp(0.0, 255.0)
        
        # 2. Gaussian Blur
        if torch.rand(1).item() > 0.5:
            attacked = self.blur_transform(attacked)
            
        # 3. Spatial Crop (torchvision interpolations avoid complex graph detachments)
        if torch.rand(1).item() > 0.5:
            # Crop 80% to 100% of the image
            crop_ratio = 0.8 + 0.2 * torch.rand(1).item()
            new_h, new_w = int(H * crop_ratio), int(W * crop_ratio)
            
            top = torch.randint(0, H - new_h + 1, (1,)).item()
            left = torch.randint(0, W - new_w + 1, (1,)).item()
            
            cropped = attacked[:, :, top:top+new_h, left:left+new_w]
            
            # Resize back to original dimensions for the extractor network
            attacked = F.interpolate(cropped, size=(H, W), mode='bilinear', align_corners=False)
            
        return attacked

    def set_phase(self, phase):
        """Updates the training curriculum phase: 1, 2, or 3."""
        if phase > 1 and self.phase == 1:
            self.phase2_steps = 0 # reset scheduler when entering phase 2
        self.phase = phase

    def train_step(self, images, true_bits):
        """
        Executes one forward/backward optimization pass.
        images: (B, C, H, W) original frames
        true_bits: (B, N) target watermark binary payload
        """
        from omni_lock.losses import bit_loss, visibility_loss, soft_parity_loss
        from omni_lock.ste import StraightThroughEstimator
        
        self.optimizer.zero_grad()
        
        # 1. Mix bits into a spatial probability mask
        spatial_mask = self.mixer(true_bits)
        
        # 2. Differentiable DCT embedding
        wm_images = self.embedder(images, spatial_mask)
        
        # 3. Curriculum-based Attacks
        if self.phase >= 3:
            # Phase 3 (Robustness): Apply heavy data augmentation
            attacked_imgs = self.apply_differentiable_attacks(wm_images)
        else:
            # Phase 1 & 2: Clean channel
            attacked_imgs = wm_images
            
        # 4. Extract watermark soft probabilities
        soft_preds = self.extractor(attacked_imgs)
        
        # 5. Calculate Image Fidelity Loss
        l_vis = visibility_loss(images, wm_images)
        
        # 6. Curriculum-based Bit and Parity Losses
        if self.phase >= 2:
            self.phase2_steps += 1
            
            # Phase 2+ (Binarize): Use Straight-Through Estimator
            ste = StraightThroughEstimator(temperature=1.0)
            hard_preds = ste(soft_preds)
            
            # Scale up BCE weight since we are using hard gradients now
            l_bit = bit_loss(hard_preds, true_bits)
            lambda_bce = 5.0 
            
            # Compute surrogate Parity Loss
            l_parity = soft_parity_loss(soft_preds, self.H_matrix)
            
            # Dynamic Parity Scheduling:
            # Slowly ramp up lambda_parity to prevent the network from collapsing
            # to all 0s or all 1s trivially just to satisfy H*X = 0 parity checks early on.
            # E.g., scales linearly to 1.0 over 1000 steps.
            lambda_parity = min(1.0, 0.001 * self.phase2_steps)
        else:
            # Phase 1 (Warmup): No STE, No Parity
            l_bit = bit_loss(soft_preds, true_bits)
            lambda_bce = 1.0
            
            l_parity = torch.tensor(0.0).to(self.device)
            lambda_parity = 0.0
            
        # Total Weighted Loss Vector
        total_loss = lambda_bce * l_bit + 10.0 * l_vis + lambda_parity * l_parity
        
        # Optimize Parameters
        total_loss.backward()
        self.optimizer.step()
        
        return {
            'loss': total_loss.item(),
            'bce_loss': l_bit.item(),
            'vis_loss': l_vis.item(),
            'parity_loss': l_parity.item() if lambda_parity > 0 else 0.0
        }
