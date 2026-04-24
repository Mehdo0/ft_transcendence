import torch
import torch.nn as nn
import torch.nn.functional as F


class QuickDrawBrain(nn.Module):
    def __init__(self):
        super(QuickDrawBrain, self).__init__()
        # Layer 1: Convolution (Magnifying glass)
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, padding=1)
        # Layer 2: Pooling (Shrinking)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        # Layer 3 is flattening, handled in forward()
        # Layer 4: Dense Output (Decision maker for 10 categories)
        self.dense = nn.Linear(in_features=16 * 14 * 14, out_features=35)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = torch.flatten(x, 1) 
        x = self.dense(x)
        return x

#   converting hexadecimal colors (#FF0000) to rgb colors (e.g., 255, 0, 0)
#   for an easier understanding from the ai
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

