"""
DeepGuard Hybrid Model Training Pipeline
========================================
Production-quality training module for the Bi-LSTM + Transformer + Auxiliary Fusion Model.
Dynamically handles synthetic mock data (development) and full-scale real SGCC datasets (production).

Key Features:
- Data-agnostic loader (`load_training_data`): auto-detects real SGCC file or generates demo dataset.
- Small-data auto-scaling: dynamically scales batch size and issues capacity warnings if N < 1000.
- Class Imbalance Handling: passes cost-sensitive `class_weight` multipliers to `model.fit()`.
- Precision-Recall AUC (AUC-PR) callback monitoring to prevent false positives under class imbalance.
- Versioned, data-source-tagged model checkpointing (`synthetic_demo` vs `real_sgcc`).

Author: Senior ML Engineer (DeepGuard Project)
"""

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import tensorflow as tf

from ml.config import (
    ARTIFACTS_DIR,
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    EARLY_STOPPING_PATIENCE,
    LR_REDUCTION_PATIENCE,
    LR_REDUCTION_FACTOR,
    MIN_LEARNING_RATE,
    MODEL_VERSION
)
from ml.preprocessing.preprocess import run_preprocessing_pipeline
from ml.models.fusion_model import build_hybrid_fusion_model

# Configure Training Logger
logger = logging.getLogger("DeepGuard.Training")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_training_data(
    csv_file_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Data-agnostic dataset loader.
    If `csv_file_path` exists on disk, processes the real dataset.
    If no file is found, generates a synthetic demo dataset for pipeline validation.

    Args:
        csv_file_path (Optional[str]): Path to input CSV file.
        config (Optional[Dict[str, Any]]): Preprocessing configuration options.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any], str]:
            - dataset_splits: Dictionary containing train/val/test data splits
            - quality_report: Data quality metrics and loss weights
            - data_source_tag: String identifier ("real_sgcc" or "synthetic_demo")
    """
    target_path = csv_file_path
    if target_path is None:
        # Check standard default locations
        candidate_paths = [
            "ml/data/raw/data.csv",
            "ml/data/raw/sgcc_data.csv",
            "ml/data/raw/sgcc.csv"
        ]
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                target_path = candidate
                break

    if target_path and os.path.exists(target_path):
        logger.info(f"Loading REAL SGCC dataset from: {target_path}")
        data_source_tag = "real_sgcc"
        dataset_splits, quality_report = run_preprocessing_pipeline(
            target_path,
            config=config,
            apply_smote_on_features=False
        )
    else:
        logger.warning(
            "RAW SGCC DATASET NOT FOUND ON DISK. Generating synthetic demo dataset for pipeline validation..."
        )
        data_source_tag = "synthetic_demo"
        
        # Generate temporary mock dataset (50 customers, 30 days)
        num_customers = 50
        num_days = 30
        date_cols = [f"2026-01-{day:02d}" for day in range(1, num_days + 1)]
        
        np.random.seed(42)
        data = []
        for i in range(num_customers):
            cons_no = f"CUST_{i:04d}"
            flag = 1 if i < 5 else 0  # 10% theft rate
            readings = np.random.uniform(5.0, 30.0, size=num_days)
            nan_idx = np.random.choice(num_days, size=2, replace=False)
            readings[nan_idx] = np.nan
            if i == 0:
                readings[3] = -15.0

            data.append([cons_no] + list(readings) + [flag])

        columns = ["CONS_NO"] + date_cols + ["FLAG"]
        mock_df = pd.DataFrame(data, columns=columns)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp_file:
            mock_df.to_csv(tmp_file.name, index=False)
            tmp_path = tmp_file.name

        try:
            dataset_splits, quality_report = run_preprocessing_pipeline(
                tmp_path,
                config=config,
                apply_smote_on_features=False
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return dataset_splits, quality_report, data_source_tag


def train_model(
    csv_file_path: Optional[str] = None,
    custom_config: Optional[Dict[str, Any]] = None
) -> Tuple[tf.keras.Model, Dict[str, Any], str, Dict[str, Any]]:
    """
    Executes model training with automatic scaling, callbacks, and checkpointing.

    Args:
        csv_file_path (Optional[str]): Path to SGCC CSV dataset file.
        custom_config (Optional[Dict[str, Any]]): Training hyperparameter overrides.

    Returns:
        Tuple[tf.keras.Model, Dict[str, Any], str, Dict[str, Any]]:
            - Trained Keras Model
            - Training history dict
            - Saved checkpoint path string
            - Data quality report dict
    """
    logger.info("=== STARTING DEEPGUARD HYBRID MODEL TRAINING ===")

    # 1. Load Data
    splits, quality_report, data_source_tag = load_training_data(csv_file_path, custom_config)

    X_seq_train = splits["train"]["X_seq"]
    X_feat_train = splits["train"]["X_feat"]
    y_train = splits["train"]["y"]

    X_seq_val = splits["val"]["X_seq"]
    X_feat_val = splits["val"]["X_feat"]
    y_val = splits["val"]["y"]

    num_train_samples = len(y_train)
    logger.info(f"Loaded Training Split: {num_train_samples} samples | Validation Split: {len(y_val)} samples")

    # 2. Dynamic Small-Data Regime Scaling
    batch_size = BATCH_SIZE
    if num_train_samples < 1000:
        batch_size = max(8, min(32, num_train_samples // 4))
        logger.warning(
            f"*************************************************************************\n"
            f"  SMALL DATASET WARNING (N_train = {num_train_samples} < 1000):\n"
            f"  Auto-adjusted batch size to {batch_size}.\n"
            f"  Results on synthetic/small data are for PIPELINE VERIFICATION ONLY\n"
            f"  and do NOT represent production theft detection performance!\n"
            f"*************************************************************************"
        )
    else:
        logger.info(f"Full Scale Training Detected (N_train = {num_train_samples:,}). Using batch size: {batch_size}")

    # 3. Fetch Class Weights
    class_weights = quality_report.get("loss_class_weights", {0: 1.0, 1: 5.0})
    logger.info(f"Using Cost-Sensitive Class Weights for Training: {class_weights}")

    # 4. Instantiate Hybrid Fusion Model
    seq_shape = (X_seq_train.shape[1], X_seq_train.shape[2])
    feat_shape = (X_feat_train.shape[1],)
    
    logger.info(f"Instantiating Hybrid Model: seq_shape={seq_shape}, feat_shape={feat_shape}")
    model = build_hybrid_fusion_model(
        seq_shape=seq_shape,
        feat_shape=feat_shape,
        learning_rate=LEARNING_RATE
    )

    # 5. Configure Callbacks
    checkpoints_dir = ARTIFACTS_DIR / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_filename = f"{data_source_tag}_fusion_{MODEL_VERSION}.keras"
    checkpoint_path = str(checkpoints_dir / checkpoint_filename)

    callbacks = [
        # Monitor val_auc_pr (Precision-Recall AUC) instead of val_loss or val_accuracy.
        # Under severe class imbalance (theft ~5-10%), val_accuracy can be 90%+ simply by predicting zero theft.
        # AUC-PR directly measures true positive recovery vs false alarm trade-offs.
        tf.keras.callbacks.EarlyStopping(
            monitor="val_auc_pr",
            mode="max",
            patience=EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_auc_pr",
            mode="max",
            save_best_only=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_auc_pr",
            mode="max",
            factor=LR_REDUCTION_FACTOR,
            patience=LR_REDUCTION_PATIENCE,
            min_lr=MIN_LEARNING_RATE,
            verbose=1
        )
    ]

    # 6. Fit Model
    logger.info(f"Starting model fit for max {EPOCHS} epochs...")
    history = model.fit(
        x=[X_seq_train, X_feat_train],
        y=y_train,
        validation_data=([X_seq_val, X_feat_val], y_val),
        epochs=EPOCHS,
        batch_size=batch_size,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1
    )

    # 7. Save History Log
    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    history_filename = f"{data_source_tag}_history_{MODEL_VERSION}.json"
    history_path = str(logs_dir / history_filename)

    history_dict = {metric: [float(val) for val in vals] for metric, vals in history.history.items()}
    with open(history_path, "w") as f:
        json.dump(history_dict, f, indent=2)

    logger.info(f"Training completed successfully.")
    logger.info(f"Best Model Checkpoint saved to: {checkpoint_path}")
    logger.info(f"Training History Log saved to: {history_path}")

    return model, history_dict, checkpoint_path, quality_report


if __name__ == "__main__":
    train_model()
