from dataclasses import dataclass


@dataclass(frozen=True)
class DrawingConfig:
    input_size: int = 4
    max_len: int = 128
    canvas_size: float = 256.0
    simplify_epsilon: float = 2.0
    min_point_distance: float = 1.0
    min_cut_len: int = 5


@dataclass(frozen=True)
class ModelConfig:
    d_model: int = 128
    nhead: int = 4
    num_layers: int = 4
    dim_feedforward: int = 512
    dropout: float = 0.1


@dataclass(frozen=True)
class TrainingConfig:
    epochs: int = 20
    batch_size: int = 128
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    scheduler_factor: float = 0.5
    scheduler_patience: int = 1
    data_dir: str = "data_clean"
    best_model_path: str = "quickdraw_transformer_perfect.pth"


@dataclass(frozen=True)
class PreprocessConfig:
    clean_data_dir: str = "data_clean"
    samples_per_class: int = 2500
    train_split: float = 0.8
    download_timeout: int = 60
    categories_url: str = "https://raw.githubusercontent.com/googlecreativelab/quickdraw-dataset/master/categories.txt"
    raw_data_url_template: str = (
        "https://storage.googleapis.com/quickdraw_dataset/full/raw/{}.ndjson"
    )


DRAWING_CONFIG = DrawingConfig()
MODEL_CONFIG = ModelConfig()
TRAINING_CONFIG = TrainingConfig()
PREPROCESS_CONFIG = PreprocessConfig()
