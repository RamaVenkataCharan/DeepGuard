"""
DeepGuard — Single Source of Truth Baseline Sanity Run
======================================================
Executes 2 clean training epochs on 300,000 real SGCC dataset windows (seed=42, batch_size=8192)
as the single baseline source of truth.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["KERAS_BACKEND"] = "tensorflow"

import json
import time
import logging
import numpy as np
import tensorflow as tf
import keras

from ml.config import ARTIFACTS_DIR, LEARNING_RATE
from ml.preprocessing.preprocess import run_preprocessing_pipeline
from ml.models.fusion_model import build_hybrid_fusion_model

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DeepGuard.SingleBaseline")

def main():
    SGCC_DATA_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "data.csv")
    splits, quality_report = run_preprocessing_pipeline(
        SGCC_DATA_PATH,
        config=None,
        apply_smote_on_features=False
    )

    SEED = 42
    np.random.seed(SEED)
    train_indices = np.random.choice(len(splits["train"]["y"]), size=300000, replace=False)
    val_indices = np.random.choice(len(splits["val"]["y"]), size=60000, replace=False)

    X_seq_train = splits["train"]["X_seq"][train_indices]
    X_feat_train = splits["train"]["X_feat"][train_indices]
    y_train = splits["train"]["y"][train_indices]

    X_seq_val = splits["val"]["X_seq"][val_indices]
    X_feat_val = splits["val"]["X_feat"][val_indices]
    y_val = splits["val"]["y"][val_indices]

    class_weights = quality_report.get("loss_class_weights", {0: 0.5466, 1: 5.8606})
    logger.info(f"SINGLE BASELINE RUN: Seed={SEED}, Train={len(y_train):,}, Val={len(y_val):,}, BatchSize=8192")
    logger.info(f"Class Weights: {class_weights}")

    keras.utils.set_random_seed(SEED)

    model = build_hybrid_fusion_model(
        seq_shape=(14, 1),
        feat_shape=(8,),
        learning_rate=LEARNING_RATE
    )

    t0 = time.time()
    history = model.fit(
        x=[X_seq_train, X_feat_train],
        y=y_train,
        validation_data=([X_seq_val, X_feat_val], y_val),
        epochs=2,
        batch_size=8192,
        class_weight=class_weights,
        verbose=1
    )
    t1 = time.time()
    total_time = t1 - t0
    logger.info(f"Baseline run completed in {total_time:.2f} seconds ({total_time/2:.2f} s/epoch)")

    hist_dict = {k: [float(x) for x in v] for k, v in history.history.items()}
    hist_dict["measured_total_seconds"] = float(total_time)
    hist_dict["measured_seconds_per_epoch"] = float(total_time / 2.0)
    hist_dict["seed"] = SEED
    hist_dict["batch_size"] = 8192

    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out_file = logs_dir / "final_clean_baseline_history.json"
    with open(out_file, "w") as f:
        json.dump(hist_dict, f, indent=2)

    print("\n" + "="*75)
    print(f"  SINGLE SOURCE OF TRUTH BASELINE RESULTS (SEED={SEED}, BATCH_SIZE=8192)")
    print("="*75)
    for ep in range(2):
        print(f"\n--- EPOCH {ep+1} ---")
        for k in sorted(history.history.keys()):
            val = history.history[k][ep]
            print(f"  {k:20s}: {val:.6f}")
    print("="*75 + "\n")

if __name__ == "__main__":
    main()
