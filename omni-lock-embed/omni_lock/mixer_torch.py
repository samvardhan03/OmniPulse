import torch
import torch.nn as nn
from omni_lock.mixer import MixerNetwork

class MixerTorch(nn.Module):
    """
    End-to-end differentiable counterpart of MixerNetwork.
    Used for training the watermark system via backpropagation.
    """
    def __init__(self, key_size=64, embed_dim=256, spatial_dim=512*512):
        super().__init__()
        # Note: the original MixerNetwork does not use bias in standard matrix multiplications.
        # Ensure bias=False to accurately mirror the inference pipeline's weight shapes.
        self.embed = nn.Linear(key_size, embed_dim, bias=False)
        
        self.token_mix_1 = nn.Linear(embed_dim, embed_dim * 2, bias=False)
        self.token_mix_2 = nn.Linear(embed_dim * 2, embed_dim, bias=False)
        
        self.channel_mix_1 = nn.Linear(embed_dim, embed_dim * 2, bias=False)
        self.channel_mix_2 = nn.Linear(embed_dim * 2, embed_dim, bias=False)
        
        self.project = nn.Linear(embed_dim, spatial_dim, bias=False)
        
    def forward(self, x):
        """
        Map watermark bits x to spatial mask.
        x: (B, key_size)
        Returns: (B, H, W) mask if appropriate reshaping is applied, or (B, spatial_dim)
        """
        # Embed
        x = self.embed(x)
        
        # Token mixing
        res = x
        x = torch.tanh(self.token_mix_1(x))
        x = self.token_mix_2(x)
        x = x + res
        
        # Channel mixing
        res = x
        x = torch.tanh(self.channel_mix_1(x))
        x = self.channel_mix_2(x)
        x = x + res
        
        x = self.project(x)
        return torch.tanh(x)
        
    def export_to_numpy(self):
        """
        Extracts PyTorch trained weights and returns an initialized instance
        of the original numpy MixerNetwork.
        """
        import math
        import numpy as np
        
        # Assume square spatial dimension for easy initialization
        h = int(math.sqrt(self.project.out_features))
        w = self.project.out_features // h
        
        numpy_mixer = MixerNetwork(input_dim=self.embed.in_features, 
                                   hidden_dim=self.embed.out_features,
                                   output_shape=(h, w))
        
        # Linear layer uses x @ W.T in PyTorch. The numpy mixer code does x @ W
        # Therefore, we transpose the PyTorch generic weights explicitly.
        numpy_mixer.embed = self.embed.weight.detach().cpu().numpy().T
        numpy_mixer.token_mix_w1 = self.token_mix_1.weight.detach().cpu().numpy().T
        numpy_mixer.token_mix_w2 = self.token_mix_2.weight.detach().cpu().numpy().T
        numpy_mixer.channel_mix_w1 = self.channel_mix_1.weight.detach().cpu().numpy().T
        numpy_mixer.channel_mix_w2 = self.channel_mix_2.weight.detach().cpu().numpy().T
        numpy_mixer.project = self.project.weight.detach().cpu().numpy().T
        
        return numpy_mixer
