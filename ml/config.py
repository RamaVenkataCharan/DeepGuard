"""
DeepGuard ML Pipeline — Centralized Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Ensure directories exist
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, ARTIFACTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Data ─────────────────────────────────────────────────────────────────────
SGCC_FILENAME = os.getenv("SGCC_FILENAME", "sgcc_data.csv")
WEATHER_FILENAME = os.getenv("WEATHER_FILENAME", "weather_data.csv")
RANDOM_SEED = 42
TEST_SIZE = 0.2
VALIDATION_SIZE = 0.15

# ── Preprocessing ────────────────────────────────────────────────────────────
SEQUENCE_LENGTHS = [7, 14, 30]
DEFAULT_SEQUENCE_LENGTH = int(os.getenv("ML_SEQUENCE_LENGTH", "14"))
SLIDING_WINDOW_STEP = 1

# Outlier detection
OUTLIER_IQR_MULTIPLIER = 3.0
OUTLIER_ZSCORE_THRESHOLD = 3.5

# Normalization
NORMALIZATION_METHOD = "minmax"  # "minmax" or "zscore"

# ── Model Architecture ───────────────────────────────────────────────────────
# Bi-LSTM branch
BILSTM_UNITS_L1 = 128
BILSTM_UNITS_L2 = 64
BILSTM_DROPOUT = 0.3
BILSTM_RECURRENT_DROPOUT = 0.2

# Transformer branch
TRANSFORMER_NUM_HEADS = 4
TRANSFORMER_FF_DIM = 128
TRANSFORMER_NUM_BLOCKS = 2
TRANSFORMER_DROPOUT = 0.2
TRANSFORMER_EMBED_DIM = 64

# Fusion
FUSION_DENSE_UNITS = [256, 128, 64]
FUSION_DROPOUT = 0.3
FUSION_METHOD = "concatenate"  # "concatenate" or "weighted_average"

# ── Training ─────────────────────────────────────────────────────────────────
BATCH_SIZE = int(os.getenv("ML_BATCH_SIZE", "32"))
EPOCHS = int(os.getenv("ML_EPOCHS", "100"))
LEARNING_RATE = float(os.getenv("ML_LEARNING_RATE", "0.001"))
EARLY_STOPPING_PATIENCE = 10
LR_REDUCTION_PATIENCE = 5
LR_REDUCTION_FACTOR = 0.5
MIN_LEARNING_RATE = 1e-6

# Class imbalance
USE_CLASS_WEIGHTS = True
USE_SMOTE = False  # Alternative to class weights

# ── Model Versioning ─────────────────────────────────────────────────────────
MODEL_VERSION = os.getenv("ML_MODEL_VERSION", "v1.0.0")
MODEL_FILENAME = f"deepguard_fusion_{MODEL_VERSION}.keras"
SCALER_FILENAME = f"scaler_{MODEL_VERSION}.joblib"

# ── Risk Score ───────────────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "low": (0, 25),
    "medium": (26, 50),
    "high": (51, 75),
    "critical": (76, 100),
}
ALERT_RISK_THRESHOLD = 51  # Generate alert if risk_score >= this value

# ── Hyperparameter Tuning ────────────────────────────────────────────────────
TUNING_PARAM_GRID = {
    "sequence_length": [7, 14, 30],
    "bilstm_units": [64, 128],
    "transformer_heads": [2, 4, 8],
    "learning_rate": [0.001, 0.0005, 0.0001],
    "batch_size": [16, 32, 64],
}
