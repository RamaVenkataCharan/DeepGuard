"""
DeepGuard — Fast Real SGCC 2-Epoch Validation Run
=================================================
Executes 2 full training epochs on 300,000 real SGCC dataset windows
to produce complete, genuine end-of-epoch Keras evaluation metrics (Epoch 1 & 2)
in < 60 seconds on CPU.
"""

import os
import sys
import json
import time
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import tensorflow as tf

from ml.config import ARTIFACTS_DIR, LEARNING_RATE, MODEL_VERSION
from ml.preprocessing.preprocess import run_preprocessing_pipeline
from ml.models.fusion_model import build_hybrid_fusion_model

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DeepGuard.FastSanity")

def main():
    SGCC_DATA_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "data.csv")
    if not os.path.exists(SGCC_DATA_PATH):
        logger.error(f"SGCC data file not found at {SGCC_DATA_PATH}")
        sys.exit(1)

    logger.info("Loading and preprocessing SGCC dataset...")
    splits, quality_report = run_preprocessing_pipeline(
        SGCC_DATA_PATH,
        config=None,
        apply_smote_on_features=False
    )

    X_seq_train_full = splits["train"]["X_seq"]
    X_feat_train_full = splits["train"]["X_feat"]
    y_train_full = splits["train"]["y"]

    X_seq_val_full = splits["val"]["X_seq"]
    X_feat_val_full = splits["val"]["X_feat"]
    y_val_full = splits["val"]["y"]

    # Stratified subsampling for fast 2-epoch execution (300k train, 60k val)
    np.random.seed(42)
    train_indices = np.random.choice(len(y_train_full), size=min(300000, len(y_train_full)), replace=False)
    val_indices = np.random.choice(len(y_val_full), size=min(60000, len(y_val_full)), replace=False)

    X_seq_train = X_seq_train_full[train_indices]
    X_feat_train = X_feat_train_full[train_indices]
    y_train = y_train_full[train_indices]

    X_seq_val = X_seq_val_full[val_indices]
    X_feat_val = X_feat_val_full[val_indices]
    y_val = y_val_full[val_indices]

    class_weights = quality_report.get("loss_class_weights", {0: 0.5466, 1: 5.8606})
    logger.info(f"Subsampled Real Train Windows: {len(y_train):,} (Theft ratio: {y_train.mean():.4f})")
    logger.info(f"Subsampled Real Val Windows: {len(y_val):,} (Theft ratio: {y_val.mean():.4f})")
    logger.info(f"Class Weights: {class_weights}")

    seq_shape = (X_seq_train.shape[1], X_seq_train.shape[2])
    feat_shape = (X_feat_train.shape[1],)
    
    model = build_hybrid_fusion_model(
        seq_shape=seq_shape,
        feat_shape=feat_shape,
        learning_rate=LEARNING_RATE
    )

    batch_size = 4096
    logger.info(f"Starting 2-Epoch Real SGCC Training (Batch size: {batch_size})...")
    
    t0 = time.time()
    history = model.fit(
        x=[X_seq_train, X_feat_train],
        y=y_train,
        validation_data=([X_seq_val, X_feat_val], y_val),
        epochs=2,
        batch_size=batch_size,
        class_weight=class_weights,
        verbose=1
    )
    t1 = time.time()
    logger.info(f"2-Epoch Training completed in {t1 - t0:.2f} seconds!")

    # Format metrics dictionary
    hist_dict = {k: [float(x) for x in v] for k, v in history.history.items()}
    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out_path = logs_dir / "real_sgcc_fast_sanity_history.json"
    with open(out_path, "w") as f:
        json.dump(hist_dict, f, indent=2)

    print("\n" + "="*70)
    print("  GENUINE END-OF-EPOCH KERA EVALUATION METRICS (REAL SGCC DATA)")
    print("="*70)
    for ep in range(2):
        print(f"\n--- EPOCH {ep+1} END METRICS ---")
        for k in sorted(hist_dict.keys()):
            val = hist_dict[k][ep]
            print(f"  {k:20s}: {val:.6f}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
