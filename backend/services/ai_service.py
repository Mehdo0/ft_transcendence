import math
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from state.config import BASE_DIR, WORD_LIST
from utils.drawing_parse import base64_to_tensor, strokes_to_tensor


# ==========================================
# 1. UTILITAIRES GLOBAUX
# ==========================================
def load_word_list():
    file_path = os.path.join(BASE_DIR, WORD_LIST)
    if not os.path.exists(file_path):
        raise ValueError(WORD_LIST, "doesnt exist")
    with open(file_path) as inp:
        data = [line.strip() for line in inp if line.strip()]
    if not data:
        raise ValueError(WORD_LIST, "is empty")
    return data

# Chargement de la liste une seule fois au démarrage
word_list = load_word_list()
device = torch.device("cpu")


# ==========================================
# 2. ARCHITECTURE CNN (VOTRE IA : Image)
# ==========================================
class QuickDrawBrain(nn.Module):
    def __init__(self):
        super(QuickDrawBrain, self).__init__()
        self.conv1_1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1_1 = nn.BatchNorm2d(32)
        self.conv1_2 = nn.Conv2d(32, 32, kernel_size=3, padding=1)
        self.bn1_2 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.conv2_1 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2_1 = nn.BatchNorm2d(64)
        self.conv2_2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.bn2_2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.fc1 = nn.Linear(in_features=64 * 7 * 7, out_features=512)
        self.bn_fc1 = nn.BatchNorm1d(512)
        self.dropout = nn.Dropout(0.4) 
        self.fc2 = nn.Linear(in_features=512, out_features=35)

    def forward(self, x):
        x = F.relu(self.bn1_1(self.conv1_1(x)))
        x = F.relu(self.bn1_2(self.conv1_2(x)))
        x = self.pool1(x)
        
        x = F.relu(self.bn2_1(self.conv2_1(x)))
        x = F.relu(self.bn2_2(self.conv2_2(x)))
        x = self.pool2(x)
        
        x = torch.flatten(x, 1)
        x = F.relu(self.bn_fc1(self.fc1(x)))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


# ==========================================
# 3. ARCHITECTURE TRANSFORMER (IA DU COLLÈGUE : Traits)
# ==========================================
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
        return x + self.pe[:, : x.size(1)]

class QuickDrawTransformer(nn.Module):
    def __init__(self, num_classes: int, input_size: int = 4, max_len: int = 128,
                 d_model: int = 128, nhead: int = 4, num_layers: int = 4,
                 dim_feedforward: int = 512, dropout: float = 0.1):
        super().__init__()
        self.input_projection = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward,
            dropout=dropout, batch_first=True
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


# ==========================================
# 4. CHARGEMENT DES DEUX MODÈLES
# ==========================================
# Chargement du CNN
cnn_model = QuickDrawBrain()
cnn_weights = torch.load(os.path.join(BASE_DIR, "ai_brain", "trained_brain.pth"), map_location=device, weights_only=True)
cnn_model.load_state_dict(cnn_weights)
cnn_model.eval()

# Chargement du Transformer
transformer_checkpoint = torch.load(os.path.join(BASE_DIR, "ai_brain", "transformers.pth"), map_location=device, weights_only=False)
transformer_model = QuickDrawTransformer(**transformer_checkpoint["model_config"]).to(device)
transformer_model.load_state_dict(transformer_checkpoint["model_state_dict"])
transformer_model.eval()


# ==========================================
# 5. PRÉDICTION COMBINÉE (ENSEMBLE)
# ==========================================
def internal_make_ai_guess(base64_string: str, strokes: list, target_word: str):
    """
    Prend l'image générée (pour le CNN) et les traits bruts (pour le Transformer),
    et combine leurs prédictions.
    """
    # Vérifications de base
    if target_word not in word_list:
        return {target_word: 0.0}
    
    target_index = word_list.index(target_word)
    src, mask, has_drawing = strokes_to_tensor(strokes)

    if not has_drawing:
        return {target_word: 0.0}

    with torch.no_grad():
        # IA 1 : Le Transformer évalue les traits (séquence)
        trans_logits = transformer_model(src, src_key_padding_mask=mask)
        trans_probs = F.softmax(trans_logits, dim=1)

        # IA 2 : Le CNN évalue l'image (pixels)
        cnn_tensor = base64_to_tensor(base64_string)
        cnn_logits = cnn_model(cnn_tensor)
        cnn_probs = F.softmax(cnn_logits, dim=1)

        # FUSION : On fait la moyenne des deux probabilités
        combined_probs = (trans_probs + cnn_probs) / 2.0

        # Extraction du score final
        target_prob = combined_probs[0][target_index].item()
        percentage = round(target_prob * 100, 2)

    return {target_word: percentage}