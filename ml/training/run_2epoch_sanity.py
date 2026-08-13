"""
DeepGuard — Bounded 2-Epoch Sanity Training Run
================================================
Purpose: Execute exactly 2 training epochs on the real SGCC dataset with
         full per-batch progress output to verify the pipeline end-to-end
         and obtain real epoch-end validation metrics.

Hardware: CPU-only (TF 2.16.2, no GPU/CUDA).
Batch size: 8192 (large to reduce step count and finish in reasonable CPU time).
Expected: ~529 steps/epoch × 2 epochs = ~1058 total steps.

Output artifacts:
  ml/artifacts/checkpoints/real_sgcc_fusion_v1.0.0.keras
  ml/artifacts/logs/real_sgcc_history_v1.0.0.json

Author: DeepGuard ML Pipeline
"""

import os
import sys
import json
import time
import logging

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import tensorflow as tf

from ml.config import (
    ARTIFACTS_DIR,
    LEARNING_RATE,
    MODEL_VERSION,
)
from ml.preprocessing.preprocess import run_preprocessing_pipeline
from ml.models.fusion_model import build_hybrid_fusion_model

# ─── Configuration ───────────────────────────────────────────────────────────
BOUNDED_EPOCHS = 2
BOUNDED_BATCH_SIZE = 8192  # Large batch for CPU feasibility (~529 steps/epoch)
SGCC_DATA_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "data.csv")

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DeepGuard.SanityRun")


def main():
    t_start = time.time()

    # ── 1. Hardware check ────────────────────────────────────────────────────
    gpus = tf.config.list_physical_devices("GPU")
    logger.info(f"TensorFlow version: {tf.__version__}")
    logger.info(f"GPUs detected: {len(gpus)} — {'GPU' if gpus else 'CPU-ONLY'} execution")
    if gpus:
        for g in gpus:
            logger.info(f"  GPU device: {g}")

    # ── 2. Verify dataset file exists ────────────────────────────────────────
    if not os.path.exists(SGCC_DATA_PATH):
        logger.error(f"SGCC dataset NOT FOUND at: {SGCC_DATA_PATH}")
        logger.error("Cannot proceed. Place data.csv in ml/data/raw/ first.")
        sys.exit(1)

    file_size_mb = os.path.getsize(SGCC_DATA_PATH) / (1024 * 1024)
    logger.info(f"SGCC dataset found: {SGCC_DATA_PATH} ({file_size_mb:.2f} MB)")

    # ── 3. Run preprocessing pipeline ───────────────────────────────────────
    logger.info("Starting preprocessing pipeline (this may take ~2 minutes)...")
    t_preprocess = time.time()
    dataset_splits, quality_report = run_preprocessing_pipeline(
        SGCC_DATA_PATH,
        config=None,
        apply_smote_on_features=False,
    )
    dt_preprocess = time.time() - t_preprocess
    logger.info(f"Preprocessing completed in {dt_preprocess:.1f}s")

    X_seq_train = dataset_splits["train"]["X_seq"]
    X_feat_train = dataset_splits["train"]["X_feat"]
    y_train = dataset_splits["train"]["y"]

    X_seq_val = dataset_splits["val"]["X_seq"]
    X_feat_val = dataset_splits["val"]["X_feat"]
    y_val = dataset_splits["val"]["y"]

    n_train = len(y_train)
    n_val = len(y_val)
    steps_per_epoch = int(np.ceil(n_train / BOUNDED_BATCH_SIZE))

    logger.info(f"Train samples: {n_train:,} | Val samples: {n_val:,}")
    logger.info(f"Batch size: {BOUNDED_BATCH_SIZE} | Steps/epoch: {steps_per_epoch}")
    logger.info(f"Total steps for 2 epochs: {steps_per_epoch * 2}")

    # ── 4. Class weights ─────────────────────────────────────────────────────
    class_weights = quality_report.get("loss_class_weights", {0: 1.0, 1: 5.0})
    logger.info(f"Class weights: {class_weights}")

    # ── 5. Build model ───────────────────────────────────────────────────────
    seq_shape = (X_seq_train.shape[1], X_seq_train.shape[2])
    feat_shape = (X_feat_train.shape[1],)
    logger.info(f"Building model: seq_shape={seq_shape}, feat_shape={feat_shape}")

    model = build_hybrid_fusion_model(
        seq_shape=seq_shape,
        feat_shape=feat_shape,
        learning_rate=LEARNING_RATE,
    )
    model.summary(print_fn=logger.info)

    # ── 6. Callbacks (minimal — no early stopping for bounded run) ───────────
    checkpoints_dir = ARTIFACTS_DIR / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = str(checkpoints_dir / f"real_sgcc_fusion_{MODEL_VERSION}.keras")

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_auc_pr",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
    ]

    # ── 7. Train ─────────────────────────────────────────────────────────────
    logger.info(f"=== STARTING 2-EPOCH BOUNDED TRAINING RUN ===")
    logger.info(f"Estimated time: {steps_per_epoch * 2 * 1.7 / 60:.0f}–{steps_per_epoch * 2 * 2.5 / 60:.0f} minutes on CPU")

    t_train = time.time()
    history = model.fit(
        x=[X_seq_train, X_feat_train],
        y=y_train,
        validation_data=([X_seq_val, X_feat_val], y_val),
        epochs=BOUNDED_EPOCHS,
        batch_size=BOUNDED_BATCH_SIZE,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,  # Full per-batch progress
    )
    dt_train = time.time() - t_train

    # ── 8. Save history ──────────────────────────────────────────────────────
    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    history_path = str(logs_dir / f"real_sgcc_history_{MODEL_VERSION}.json")

    history_dict = {
        metric: [float(val) for val in vals]
        for metric, vals in history.history.items()
    }
    with open(history_path, "w") as f:
        json.dump(history_dict, f, indent=2)

    # ── 9. Print final results ───────────────────────────────────────────────
    dt_total = time.time() - t_start

    print("\n" + "=" * 72)
    print("  DEEPGUARD 2-EPOCH SANITY RUN — FINAL RESULTS")
    print("=" * 72)
    print(f"  Hardware            : {'GPU (' + str(gpus) + ')' if gpus else 'CPU-only'}")
    print(f"  TensorFlow          : {tf.__version__}")
    print(f"  Dataset             : REAL SGCC ({n_train:,} train / {n_val:,} val)")
    print(f"  Batch size          : {BOUNDED_BATCH_SIZE}")
    print(f"  Training time       : {dt_train:.1f}s ({dt_train/60:.1f} min)")
    print(f"  Total wall time     : {dt_total:.1f}s ({dt_total/60:.1f} min)")
    print("-" * 72)

    for epoch_idx in range(BOUNDED_EPOCHS):
        print(f"\n  --- Epoch {epoch_idx + 1}/{BOUNDED_EPOCHS} ---")
        for metric_name in sorted(history_dict.keys()):
            if epoch_idx < len(history_dict[metric_name]):
                val = history_dict[metric_name][epoch_idx]
                print(f"    {metric_name:25s}: {val:.6f}")

    print("\n" + "-" * 72)
    print(f"  Checkpoint saved to : {checkpoint_path}")
    print(f"  History saved to    : {history_path}")
    print("=" * 72 + "\n")

    return history_dict


if __name__ == "__main__":
    main()
