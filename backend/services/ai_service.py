import math
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from state.config import BASE_DIR, WORD_LIST
from utils.drawing_parse import strokes_to_tensor


def load_word_list():
    FILE_PATH = os.path.join(BASE_DIR, WORD_LIST)
    if not os.path.exists(FILE_PATH):
        raise ValueError(WORD_LIST, "doesnt exist")
    with open(FILE_PATH) as inp:
        data = []
        for line in inp:
            word = line.strip()
            if word:
                data.append(word)
    if not data:
        raise ValueError(WORD_LIST, "is empty")
    return data


# class QuickDrawBrain(nn.Module):
#     def __init__(self):
#         super(QuickDrawBrain, self).__init__()

#         # BLOCK 1: First set of magnifying glasses (Looks for basic edges/curves)
#         # We upgraded out_channels to 32 (32 different magnifying glasses)
#         self.conv1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
#         self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

#         # BLOCK 2: Second set of magnifying glasses (Combines edges into complex shapes)
#         # Takes the 32 channels from Block 1 and uses 64 new magnifying glasses
#         self.conv2 = nn.Conv2d(
#             in_channels=32, out_channels=64, kernel_size=3, padding=1
#         )
#         self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

#         # DROPOUT: Randomly turns off 25% of brain connections during training
#         # to force the AI to build stronger, more generalized pathways
#         self.dropout = nn.Dropout(0.25)

#         # BLOCK 3: The Decision Makers
#         # Math Check: Our 28x28 image went through pool1 (shrunk to 14x14)
#         # and pool2 (shrunk to 7x7).
#         # 64 channels * 7 height * 7 width = 3136 flattened pixels
#         self.fc1 = nn.Linear(
#             in_features=64 * 7 * 7, out_features=512
#         )  # A deep hidden layer
#         self.fc2 = nn.Linear(
#             in_features=512, out_features=35
#         )  # Final output for 35 categories

#     def forward(self, x):
#         # Pass through Block 1
#         x = F.relu(self.conv1(x))
#         x = self.pool1(x)

#         # Pass through Block 2
#         x = F.relu(self.conv2(x))
#         x = self.pool2(x)

#         # Flatten the 3D grid into a 1D line
#         x = torch.flatten(x, 1)

#         # Pass through the new deep layers with Dropout
#         x = F.relu(self.fc1(x))
#         x = self.dropout(x)
#         x = self.fc2(x)
#         return x


# model = QuickDrawBrain()
# BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "trained_brain.pth")
# map_location = torch.device("cpu")
# # Force PyTorch to use the local CPU
# device = torch.device("cpu")
# # Translate the GPU math to CPU math while loading
# weights = torch.load(BRAIN_PATH, map_location=device, weights_only=True)
# model.load_state_dict(weights)
# model.eval()

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 200):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]

class QuickDrawTransformer(nn.Module):
    def __init__(
        self,
        num_classes: int,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_projection = nn.Linear(3, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc_out = nn.Linear(d_model, num_classes)

    def forward(self, src: torch.Tensor, src_key_padding_mask: torch.Tensor) -> torch.Tensor:
        x = self.input_projection(src)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
        masked_x = x.masked_fill(src_key_padding_mask.unsqueeze(-1), 0.0)
        actual_lengths = (~src_key_padding_mask).sum(dim=1, keepdim=True).clamp(min=1)
        mean_pooled = masked_x.sum(dim=1) / actual_lengths
        return self.fc_out(mean_pooled)

word_list = load_word_list()
device = torch.device("cpu")
model = QuickDrawTransformer(num_classes=len(word_list)).to(device)

BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "transformers.pth")
weights = torch.load(BRAIN_PATH, map_location=device, weights_only=True)
model.load_state_dict(weights)
model.eval()

def internal_make_ai_guess(strokes: list, target_word: str):
    src, mask, has_drawing = strokes_to_tensor(strokes)

    if not has_drawing:
        return {target_word: 0.0}

    with torch.no_grad():
        logits = model(src, src_key_padding_mask=mask)
        probabilities = F.softmax(logits, dim=1)
        


    if target_word not in word_list:
        return {target_word: 0.0}

    target_index = word_list.index(target_word)
    target_score = round(probabilities[0][target_index].item() * 100, 2)

    return {target_word: target_score}
