import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18

OBSERVATIONS = ["acne_like_features", "redness", "dark_spots", "oiliness", "dryness", "uneven_tone", "texture", "fine_lines"]
SKIN_TYPES = ["normal", "dry", "oily", "combination"]

class SkinObservationNet(nn.Module):
    """ResNet-18 transfer-learning backbone with independent observation and skin-type heads."""
    def __init__(self, pretrained: bool = False):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = resnet18(weights=weights)
        features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        self.observation_head = nn.Linear(features, len(OBSERVATIONS))
        self.skin_type_head = nn.Linear(features, len(SKIN_TYPES))

    def forward(self, inputs):
        features = self.backbone(inputs)
        return self.observation_head(features), self.skin_type_head(features)