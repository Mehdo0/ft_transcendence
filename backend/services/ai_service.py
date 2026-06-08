import math
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from state.config import BASE_DIR, WORD_LIST
from utils.drawing_parse import strokes_to_tensor


BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "transformers.pth")
device = torch.device("cpu")
checkpoint = torch.load(BRAIN_PATH, map_location=device, weights_only=False)


def load_word_list():
    checkpoint_classes = checkpoint.get("classes", [])

    if checkpoint_classes:
        return checkpoint_classes

    file_path = os.path.join(BASE_DIR, WORD_LIST)

    if not os.path.exists(file_path):
        raise ValueError(WORD_LIST, "doesnt exist")

    with open(file_path) as inp:
        data = []

        for line in inp:
            word = line.strip()

            if word:
                data.append(word)

    if not data:
        raise ValueError(WORD_LIST, "is empty")

    return data


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.size(1) > self.pe.size(1):
            raise ValueError(f"Sequence too long: {x.size(1)} > {self.pe.size(1)}")

        return x + self.pe[:, : x.size(1)]


class QuickDrawTransformer(nn.Module):
    def __init__(
        self,
        num_classes: int,
        input_size: int = 4,
        max_len: int = 128,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_projection = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len)
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
model_config = checkpoint["model_config"]

if model_config["num_classes"] != len(word_list):
    raise ValueError("AI checkpoint classes do not match model config")

model = QuickDrawTransformer(**model_config).to(device)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()


def internal_make_ai_guess(strokes: list, target_word: str):
    src, mask, has_drawing = strokes_to_tensor(strokes)

    if not has_drawing:
        return {target_word: 0.0}

    if target_word not in word_list:
        return {target_word: 0.0}

    src = src.to(device)
    mask = mask.to(device)

    with torch.no_grad():
        logits = model(src, src_key_padding_mask=mask)
        probabilities = F.softmax(logits, dim=1)

    target_index = word_list.index(target_word)
    target_score = round(probabilities[0][target_index].item() * 100, 2)

    return {target_word: target_score}
