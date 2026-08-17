import os
import random

import torch
from torch.utils.data import Dataset

from config import DRAWING_CONFIG


def validate_points(points, file_path: str) -> None:
    shape = getattr(points, "shape", None)

    if shape is None or len(shape) != 2 or shape[1] != DRAWING_CONFIG.input_size:
        raise ValueError(f"Invalid data in {file_path}: shape {shape}.")


class QuickDrawCleanDataset(Dataset):
    def __init__(self, data_dir: str, classes: list[str], split: str, is_training: bool):
        self.is_training = is_training
        self.samples = []
        self.labels = []

        for class_index, class_name in enumerate(classes):
            file_path = os.path.join(data_dir, f"{class_name.replace(' ', '_')}.pth")

            if not os.path.exists(file_path):
                continue

            data = torch.load(file_path, weights_only=False)

            for points in data[split]:
                validate_points(points, file_path)

                if len(points) > 0:
                    self.samples.append(points)
                    self.labels.append(class_index)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        points = self.samples[index]

        if self.is_training and len(points) > DRAWING_CONFIG.min_cut_len:
            upper_bound = min(len(points), DRAWING_CONFIG.max_len)
            cutoff = random.randint(DRAWING_CONFIG.min_cut_len, upper_bound)
            points = points[:cutoff]
        elif len(points) > DRAWING_CONFIG.max_len:
            points = points[: DRAWING_CONFIG.max_len]

        return torch.tensor(points, dtype=torch.float32), self.labels[index]


def quickdraw_clean_collate_fn(batch): #update format so each draw has the same ammount of movements in the same batch (requiered by [pytorch])
    points_list = [item[0] for item in batch]
    labels = [item[1] for item in batch]
    lengths = [len(points) for points in points_list]
    batch_size = len(batch)
    max_length = max(lengths)
    input_size = points_list[0].shape[-1]
    inputs = torch.zeros(batch_size, max_length, input_size)
    mask = torch.zeros(batch_size, max_length, dtype=torch.bool)

    for index, points in enumerate(points_list):
        end = lengths[index]
        inputs[index, :end, :] = points
        mask[index, end:] = True

    return inputs, mask, torch.tensor(labels, dtype=torch.long)
