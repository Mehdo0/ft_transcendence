import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from backend.drawing_parse import base64_to_tensor
from backend.global_var import BASE_DIR


def load_word_list(file_name):
    FILE_PATH = os.path.join(BASE_DIR, file_name)
    if not os.path.exists(FILE_PATH):
        return {"Error": "no word list"}
    with open(FILE_PATH) as inp:
        data = inp.read().split()
    if not data:
        return {"Error": "no data in word list"}
    return data


class QuickDrawBrain(nn.Module):
    def __init__(self):
        super(QuickDrawBrain, self).__init__()

        # BLOCK 1: First set of magnifying glasses (Looks for basic edges/curves)
        # We upgraded out_channels to 32 (32 different magnifying glasses)
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        # BLOCK 2: Second set of magnifying glasses (Combines edges into complex shapes)
        # Takes the 32 channels from Block 1 and uses 64 new magnifying glasses
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        # DROPOUT: Randomly turns off 25% of brain connections during training
        # to force the AI to build stronger, more generalized pathways
        self.dropout = nn.Dropout(0.25)

        # BLOCK 3: The Decision Makers
        # Math Check: Our 28x28 image went through pool1 (shrunk to 14x14)
        # and pool2 (shrunk to 7x7).
        # 64 channels * 7 height * 7 width = 3136 flattened pixels
        self.fc1 = nn.Linear(in_features=64 * 7 * 7, out_features=512) # A deep hidden layer
        self.fc2 = nn.Linear(in_features=512, out_features=35)         # Final output for 35 categories

    def forward(self, x):
        # Pass through Block 1
        x = F.relu(self.conv1(x))
        x = self.pool1(x)

        # Pass through Block 2
        x = F.relu(self.conv2(x))
        x = self.pool2(x)

        # Flatten the 3D grid into a 1D line
        x = torch.flatten(x, 1)

        # Pass through the new deep layers with Dropout
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


model = QuickDrawBrain()
BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "trained_brain.pth")
# Force PyTorch to use the local CPU
device = torch.device('cpu')
# Translate the GPU math to CPU math while loading
weights = torch.load(BRAIN_PATH, map_location=device, weights_only=True)
model.load_state_dict(weights)
model.eval()


def make_ai_guess(base64_string):
    with torch.no_grad():
        input_tensor = base64_to_tensor(base64_string)
        drawing_output = model(input_tensor)
        probabilities = F.softmax(drawing_output, dim=1)
        top_probs, top_indices = torch.topk(probabilities, 3)
        top_probs = top_probs[0].tolist()
        top_indices = top_indices[0].tolist()
        results = {}
        word_list = load_word_list("list.txt")
        for i in range(3):
            word = word_list[top_indices[i]]
            percentage = round(top_probs[i] * 100, 2)
            results[word] = percentage

        return results
