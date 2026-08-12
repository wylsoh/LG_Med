"""
Auxiliary attribute heads supervised by parsed text keywords.

Given a pooled segmentation feature (from the decoder), three small heads
predict the attributes extracted from the text prompt by regex:
    - nature   : 2 classes   (unilateral / bilateral)            -> BCEWithLogits
    - quantity : 4 classes   (1 / 2 / 3 / 4 infected areas)      -> CrossEntropy
    - location : 6 logits    (multi-hot of 6 lung zones)         -> BCEWithLogits

This adds a multi-task regularization: the visual feature is encouraged to
encode the same properties described in the text, using the parsed keywords
as supervision. Everything is opt-in (see use_aux in config).
"""

import torch
import torch.nn as nn


class AuxHeads(nn.Module):
    """Small attribute classification heads on a pooled feature [B, in_dim]."""

    def __init__(self, in_dim: int = 96, hidden: int = 128):
        super(AuxHeads, self).__init__()

        self.nature_head = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, 2),
        )
        self.quantity_head = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, 4),
        )
        self.location_head = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, 6),
        )

    def forward(self, feat):
        """feat: [B, in_dim] pooled feature.

        Returns dict with logits:
            nature   : [B, 2]
            quantity : [B, 4]
            location : [B, 6]
        """
        return {
            'nature': self.nature_head(feat),
            'quantity': self.quantity_head(feat),
            'location': self.location_head(feat),
        }
