import torch
import torch.nn as nn

class StraightThroughEstimator(nn.Module):
    """
    Implements the Straight-Through Estimator (STE) for binarizing soft probabilities
    while preserving gradients for backpropagation.
    """
    def __init__(self, temperature=1.0):
        super().__init__()
        self.temperature = temperature

    def forward(self, soft_probs):
        """
        soft_probs: (B, ...). Output of an extraction network, typically raw logits or scaled values.
        Returns hard binary decisions (0 or 1) during forward pass, 
        and gradients as if the operation was continuous during backward pass.
        """
        # Optionally apply temperature scaling: soft = torch.sigmoid(soft_probs / self.temperature)
        # Assuming soft_probs is already bounded between [0, 1] usually, but if not:
        # soft_vals = torch.sigmoid(soft_probs / self.temperature)
        
        # We will assume soft_probs are already bounded probabilities from [0, 1] 
        # based on the prompt "Optionally scale the soft values via a sigmoid before the STE".
        # If they are arbitrary floats, sigmoid enforces prob logic. Let's do it to be safe.
        soft_vals = torch.sigmoid(soft_probs / self.temperature)
        
        # Binarize
        hard = (soft_vals > 0.5).float()
        
        # Calculate the returned variable with the STE trick
        output = soft_vals + (hard - soft_vals).detach()
        return output
