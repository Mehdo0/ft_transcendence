import torch
import torch.nn as nn
import torch.nn.functional as F
from backend.drawing_parse import base64_to_tensor
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_word_list(file_name):
    FILE_PATH = os.path.join(BASE_DIR, file_name)
    if not os.path.exists(FILE_PATH):
        return {"Error":"no word list"}
    with open(FILE_PATH) as inp:
        data = inp.read().split()
    if not data:
        return {"Error":"no data in word list"}
    return data

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

model = QuickDrawBrain()
BRAIN_PATH = os.path.join(BASE_DIR, "ai_brain", "trained_brain.pth")
weights = torch.load(BRAIN_PATH, weights_only=True)
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