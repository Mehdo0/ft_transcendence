import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from utils.drawing_parse import base64_to_tensor
from state.config import BASE_DIR, WORD_LIST


def load_word_list():
    FILE_PATH = os.path.join(BASE_DIR, WORD_LIST)
    if not os.path.exists(FILE_PATH):
        raise ValueError(WORD_LIST, "doesnt exist")
    with open(FILE_PATH) as inp:
        data = inp.read().split()
    if not data:
        raise ValueError(WORD_LIST, "is empty")
    return data


# ==================================================
# LE NOUVEAU CERVEAU AMÉLIORÉ (VGG-style + BatchNorm)
# ==================================================
class QuickDrawBrain(nn.Module):
    def __init__(self):
        super(QuickDrawBrain, self).__init__()
        
        # BLOCK 1: 28x28 -> 14x14
        self.conv1_1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1_1 = nn.BatchNorm2d(32)
        self.conv1_2 = nn.Conv2d(32, 32, kernel_size=3, padding=1)
        self.bn1_2 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # BLOCK 2: 14x14 -> 7x7
        self.conv2_1 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2_1 = nn.BatchNorm2d(64)
        self.conv2_2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.bn2_2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # BLOCK 3: Les décideurs profonds
        self.fc1 = nn.Linear(in_features=64 * 7 * 7, out_features=512)
        self.bn_fc1 = nn.BatchNorm1d(512)
        self.dropout = nn.Dropout(0.4) 
        self.fc2 = nn.Linear(in_features=512, out_features=35)

    def forward(self, x):
        # Passage dans le Bloc 1
        x = F.relu(self.bn1_1(self.conv1_1(x)))
        x = F.relu(self.bn1_2(self.conv1_2(x)))
        x = self.pool1(x)
        
        # Passage dans le Bloc 2
        x = F.relu(self.bn2_1(self.conv2_1(x)))
        x = F.relu(self.bn2_2(self.conv2_2(x)))
        x = self.pool2(x)
        
        # Aplatissement du réseau
        x = torch.flatten(x, 1)
        
        # Décision finale avec Dropout
        x = F.relu(self.bn_fc1(self.fc1(x)))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


# ==================================================
# CHARGEMENT DU MODÈLE SUR LE PROCESSEUR LOCAL (CPU)
# ==================================================
model = QuickDrawBrain()
BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "trained_brain_drawing.pth")

# Configuration de la redirection GPU -> CPU
device = torch.device("cpu")
weights = torch.load(BRAIN_PATH, map_location=device, weights_only=True)
model.load_state_dict(weights)

# Désactive le Dropout et la BatchNorm pour le mode jeu
model.eval()


def internal_make_ai_guess(base64_string, target_word):
    with torch.no_grad():
        input_tensor = base64_to_tensor(base64_string)
        drawing_output = model(input_tensor)
        probabilities = F.softmax(drawing_output, dim=1)
        word_list = load_word_list()
        try:
            target_index = word_list.index(target_word)
        except ValueError:
            return {target_word: 0.0}

        target_prob = probabilities[0][target_index].item()
        percentage = round(target_prob * 100, 2)
        results = {target_word: percentage}
        return results