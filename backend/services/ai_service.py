import math
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from state.config import BASE_DIR, WORD_LIST
from utils.drawing_parse import strokes_to_tensor


BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "transformers.pth")
device = torch.device("cpu")
checkpoint = torch.load(BRAIN_PATH, map_location=device, weights_only=True)


def load_word_list():
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


class PositionalEncoding(nn.Module): #translate the order of the movements to the model
    def __init__(self, d_model: int, max_len: int):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class QuickDrawTransformer(nn.Module):
    def __init__( #architecture of the model
        self,
        num_classes: int, # number of words the model can recognize
        input_size: int = 4, #dx, dy, is_end, is_start
        max_len: int = 128, #len max of the drawing
        d_model: int = 128, #intern size of the model
        nhead: int = 4, #watch the drawing in 4 differents ways
        num_layers: int = 4, #iteration on a pattern / recognition 
        dim_feedforward: int = 512, #size of a layer
        dropout: float = 0.1, #training only, ignore 10% of informations to generalise
    ):
        super().__init__() #init read movement, order, scores
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

    def forward(self, src: torch.Tensor, src_key_padding_mask: torch.Tensor) -> torch.Tensor: # gives instructions on how the model has to read movements, order, return a score
        x = self.input_projection(src)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
        masked_x = x.masked_fill(src_key_padding_mask.unsqueeze(-1), 0.0)
        actual_lengths = (~src_key_padding_mask).sum(dim=1, keepdim=True).clamp(min=1)
        mean_pooled = masked_x.sum(dim=1) / actual_lengths
        return self.fc_out(mean_pooled)


word_list = load_word_list()
model_config = checkpoint["model_config"]
model = QuickDrawTransformer(**model_config).to(device) #build the model based on the config and class and load it on cpu
model.load_state_dict(checkpoint["model_state_dict"]) #give to the model the "intelligence" (weights learned)
model.eval() #make sure doesn't affect model's training


def internal_make_ai_guess(strokes: list, target_word: str):
    src, mask, has_drawing = strokes_to_tensor(strokes) # tensor = array of strokes from Pytorch, necessary to train / give to AI

    if not has_drawing:
        return {target_word: 0.0}

    if target_word not in word_list:
        return {target_word: 0.0}

    with torch.no_grad(): #doesn't train the model
        logits = model(src, src_key_padding_mask=mask) #return model's raw scores (call forward)
        probabilities = F.softmax(logits, dim=1) #raw results to probabilities

    target_index = word_list.index(target_word)
    target_score = round(probabilities[0][target_index].item() * 100, 2)

    return {target_word: target_score}
