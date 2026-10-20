"""
Model Architecture Module: Elasmobranch Classifier & Embedding Extractor.

Supported backbones (desktop / accuracy-first):
  convnext_tiny, convnext_small  — 768-dim features, LayerNorm2d pooling
  efficientnet_v2_s              — 1280-dim features

Legacy backbones (kept for backward compatibility):
  mobilenet_v3_large, mobilenet_v3_small, efficientnet_b0

Dual heads:
1. Classification Head: Multi-class Softmax with temperature scaling.
2. Embedding Head: L2-normalised feature vector for exemplar cosine matching.
3. Multi-Angle Aggregator: Ensembles evidence across multiple photos of the same specimen.
"""

import os
from pathlib import Path
os.environ["TORCH_HOME"] = str(Path(__file__).parent.parent / ".torch_cache")

from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class ElasmobranchClassifier(nn.Module):
    def __init__(
        self,
        num_classes: int = 11,
        backbone_name: str = "convnext_tiny",
        embedding_dim: int = 512,
        dropout: float = 0.3,
        pretrained: bool = True
    ):
        super().__init__()
        self.num_classes = num_classes
        self.backbone_name = backbone_name
        self.embedding_dim = embedding_dim

        # ---------- Backbone selection ----------
        if "convnext_small" in backbone_name:
            weights = models.ConvNeXt_Small_Weights.DEFAULT if pretrained else None
            base = models.convnext_small(weights=weights)
            in_features = 768
            self.features = base.features
            # ConvNeXt uses AdaptiveAvgPool2d → LayerNorm2d as its pooling block
            self.pool = nn.Sequential(base.avgpool, base.classifier[0])
        elif "convnext_tiny" in backbone_name:
            weights = models.ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
            base = models.convnext_tiny(weights=weights)
            in_features = 768
            self.features = base.features
            self.pool = nn.Sequential(base.avgpool, base.classifier[0])
        elif "efficientnet_v2_s" in backbone_name:
            weights = models.EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
            base = models.efficientnet_v2_s(weights=weights)
            in_features = base.classifier[1].in_features  # 1280
            self.features = base.features
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
        elif "mobilenet_v3_large" in backbone_name:
            weights = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
            base = models.mobilenet_v3_large(weights=weights)
            in_features = base.classifier[0].in_features
            self.features = base.features
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
        elif "mobilenet_v3_small" in backbone_name:
            weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
            base = models.mobilenet_v3_small(weights=weights)
            in_features = base.classifier[0].in_features
            self.features = base.features
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
        elif "efficientnet" in backbone_name:
            # efficientnet_b0 — kept for backward compatibility
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            base = models.efficientnet_b0(weights=weights)
            in_features = base.classifier[1].in_features
            self.features = base.features
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
        else:
            # Default fallback to ConvNeXt-Tiny
            weights = models.ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
            base = models.convnext_tiny(weights=weights)
            in_features = 768
            self.features = base.features
            self.pool = nn.Sequential(base.avgpool, base.classifier[0])

        # Metric embedding projection head (L2 normalized)
        self.embedding_head = nn.Sequential(
            nn.Linear(in_features, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout)
        )

        # Classification logits head
        self.classifier = nn.Linear(embedding_dim, num_classes)

        # Calibrated temperature scaling parameter for probabilities
        self.temperature = nn.Parameter(torch.ones(1) * 1.0)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract raw pooled feature map."""
        feat = self.features(x)
        feat = self.pool(feat)
        feat = torch.flatten(feat, 1)
        return feat

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        Returns:
            logits: (batch_size, num_classes)
            normalized_embeddings: (batch_size, embedding_dim)
        """
        raw_feat = self.extract_features(x)
        emb = self.embedding_head(raw_feat)
        norm_emb = F.normalize(emb, p=2, dim=1)
        logits = self.classifier(emb)
        return logits, norm_emb

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Compute temperature-scaled class probabilities."""
        logits, _ = self.forward(x)
        scaled_logits = logits / torch.clamp(self.temperature, min=0.1, max=5.0)
        return F.softmax(scaled_logits, dim=-1)

    def predict_multi_angle(self, images_tensor: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Aggregate predictions across multiple photos of the same specimen.
        Args:
            images_tensor: (N, 3, H, W) where N is number of submitted photos
        Returns:
            mean_probs: (num_classes,)
            pooled_embedding: (embedding_dim,)
        """
        self.eval()
        with torch.no_grad():
            logits, embeddings = self.forward(images_tensor)
            scaled_logits = logits / torch.clamp(self.temperature, min=0.1, max=5.0)
            probs = F.softmax(scaled_logits, dim=-1)
            # Ensemble pooling: average probabilities across all angles
            mean_probs = torch.mean(probs, dim=0)
            pooled_emb = F.normalize(torch.mean(embeddings, dim=0, keepdim=True), p=2, dim=1).squeeze(0)

        return {
            "probabilities": mean_probs,
            "individual_probabilities": probs,
            "pooled_embedding": pooled_emb
        }
