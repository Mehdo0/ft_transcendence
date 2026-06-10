import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, Generator

import torch

from config import DRAWING_CONFIG, PREPROCESS_CONFIG
from process_drawing import process_drawing


def download_categories(categories_path: str) -> None:
    urllib.request.urlretrieve(PREPROCESS_CONFIG.categories_url, categories_path)


def load_categories() -> list[str]:
    os.makedirs(PREPROCESS_CONFIG.clean_data_dir, exist_ok=True)
    categories_path = os.path.join(PREPROCESS_CONFIG.clean_data_dir, "categories.txt")

    if not os.path.exists(categories_path):
        download_categories(categories_path)

    with open(categories_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def class_file_name(class_name: str) -> str:
    return class_name.replace(" ", "_")


def class_url(class_name: str) -> str:
    encoded_name = urllib.parse.quote(class_name, safe="")
    return PREPROCESS_CONFIG.raw_data_url_template.format(encoded_name)


def stream_quickdraw_url(file_url: str, timeout: int) -> Generator[Dict[str, Any], None, None]:
    with urllib.request.urlopen(file_url, timeout=timeout) as response:
        for line in response:
            if not line.strip():
                continue

            drawing_data = json.loads(line)

            if drawing_data.get("recognized", False):
                yield drawing_data


def metadata() -> dict:
    return {
        "input_size": DRAWING_CONFIG.input_size,
        "canvas_size": DRAWING_CONFIG.canvas_size,
        "simplify_epsilon": DRAWING_CONFIG.simplify_epsilon,
        "min_point_distance": DRAWING_CONFIG.min_point_distance,
        "samples_per_class": PREPROCESS_CONFIG.samples_per_class,
        "train_split": PREPROCESS_CONFIG.train_split,
    }


def is_ready(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False

    try:
        data = torch.load(file_path, map_location="cpu", weights_only=False)
    except Exception:
        return False

    return isinstance(data, dict) and data.get("metadata") == metadata()


def collect_drawings(class_name: str) -> list:
    drawings = []

    for drawing in stream_quickdraw_url(class_url(class_name), PREPROCESS_CONFIG.download_timeout):
        try:
            points = process_drawing(drawing["drawing"])
        except Exception:
            continue

        if len(points) == 0:
            continue

        drawings.append(points)

        if len(drawings) >= PREPROCESS_CONFIG.samples_per_class:
            break

    return drawings


def save_class(file_path: str, drawings: list) -> None:
    split_index = int(len(drawings) * PREPROCESS_CONFIG.train_split)
    torch.save(
        {
            "train": drawings[:split_index],
            "val": drawings[split_index:],
            "metadata": metadata(),
        },
        file_path,
    )


def preprocess() -> None:
    classes = load_categories()
    processed = 0
    skipped = 0

    print(f"Classes: {len(classes)}")

    for index, class_name in enumerate(classes, start=1):
        file_path = os.path.join(PREPROCESS_CONFIG.clean_data_dir, f"{class_file_name(class_name)}.pth")

        if is_ready(file_path):
            skipped += 1
            continue

        print(f"{index}/{len(classes)} {class_name}")
        drawings = collect_drawings(class_name)
        save_class(file_path, drawings)
        processed += 1

    print(f"Done: processed={processed} skipped={skipped}")


if __name__ == "__main__":
    preprocess()
