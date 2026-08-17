import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from config import DRAWING_CONFIG, MODEL_CONFIG, TRAINING_CONFIG
from dataset import QuickDrawCleanDataset, quickdraw_clean_collate_fn
from model import QuickDrawTransformer


def load_classes() -> list[str]:
    categories_path = os.path.join(TRAINING_CONFIG.data_dir, "categories.txt")

    if not os.path.exists(categories_path):
        raise FileNotFoundError("Run preprocess.py before train.py.")

    with open(categories_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def make_model_config(num_classes: int) -> dict:
    return {
        "num_classes": num_classes,
        "input_size": DRAWING_CONFIG.input_size,
        "max_len": DRAWING_CONFIG.max_len,
        "d_model": MODEL_CONFIG.d_model,
        "nhead": MODEL_CONFIG.nhead,
        "num_layers": MODEL_CONFIG.num_layers,
        "dim_feedforward": MODEL_CONFIG.dim_feedforward,
        "dropout": MODEL_CONFIG.dropout,
    }


def make_loaders(classes: list[str]) -> tuple[DataLoader, DataLoader]: #prepare datas for training and check
    train_dataset = QuickDrawCleanDataset(TRAINING_CONFIG.data_dir, classes, split="train", is_training=True)
    val_dataset = QuickDrawCleanDataset(TRAINING_CONFIG.data_dir, classes, split="val", is_training=False)

    train_loader = DataLoader(
        train_dataset,
        batch_size=TRAINING_CONFIG.batch_size,
        shuffle=True,
        collate_fn=quickdraw_clean_collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=TRAINING_CONFIG.batch_size,
        shuffle=False,
        collate_fn=quickdraw_clean_collate_fn,
    )
    return train_loader, val_loader


def train_one_epoch(
    model: QuickDrawTransformer,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_seen = 0

    for inputs, masks, labels in loader:
        inputs = inputs.to(device)
        masks = masks.to(device)
        labels = labels.to(device)

        optimizer.zero_grad(set_to_none=True) #forgot previous calculated corrections
        outputs = model(inputs, src_key_padding_mask=masks) #model predicts the batch
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * inputs.size(0)
        total_correct += (outputs.argmax(dim=1) == labels).sum().item()
        total_seen += labels.size(0)

    return total_loss / total_seen, total_correct / total_seen * 100.0


def validate(
    model: QuickDrawTransformer,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_seen = 0

    with torch.no_grad():
        for inputs, masks, labels in loader:
            inputs = inputs.to(device)
            masks = masks.to(device)
            labels = labels.to(device)
            outputs = model(inputs, src_key_padding_mask=masks)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * inputs.size(0)
            total_correct += (outputs.argmax(dim=1) == labels).sum().item()
            total_seen += labels.size(0)

    return total_loss / total_seen, total_correct / total_seen * 100.0


def save_best_model(
    model: QuickDrawTransformer,
    model_config: dict,
    classes: list[str],
    epoch: int,
    best_val_acc: float,
) -> None:
    torch.save(
        {
            "epoch": epoch,
            "best_val_acc": best_val_acc,
            "model_config": model_config,
            "classes": classes,
            "model_state_dict": model.state_dict(),
        },
        TRAINING_CONFIG.best_model_path,
    )


def train() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    classes = load_classes()
    model_config = make_model_config(len(classes))
    train_loader, val_loader = make_loaders(classes)
    model = QuickDrawTransformer(**model_config).to(device)
    criterion = nn.CrossEntropyLoss() #rule to check how wrong or right is the model
    optimizer = torch.optim.AdamW( #hwo to edit the model weights to optimize the model affter each batch
        model.parameters(),
        lr=TRAINING_CONFIG.learning_rate,
        weight_decay=TRAINING_CONFIG.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(#similar but after eacch epoch
        optimizer,
        mode="max",
        factor=TRAINING_CONFIG.scheduler_factor,
        patience=TRAINING_CONFIG.scheduler_patience,
    )
    best_val_acc = 0.0

    print(f"Device: {device}")
    print(f"Classes: {len(classes)}")
    print(f"Epochs: {TRAINING_CONFIG.epochs}")

    for epoch in range(TRAINING_CONFIG.epochs):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step(val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_best_model(model, model_config, classes, epoch + 1, best_val_acc)

        print(
            f"Epoch {epoch + 1:02d}/{TRAINING_CONFIG.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.2f}% | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.2f}%"
        )

    print(f"Done: best_val_acc={best_val_acc:.2f}%")


if __name__ == "__main__":
    train()
