"""
DeepGuard Hybrid Model Evaluation & Metric Analysis Module
==========================================================
Evaluates trained hybrid Bi-LSTM + Transformer models on test splits.
Calculates optimal decision thresholds, confusion matrices, and imbalanced classification metrics.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    precision_recall_curve,
    auc,
    confusion_matrix
)

from ml.config import ARTIFACTS_DIR, MODEL_VERSION
from ml.models.train import load_training_data

logger = logging.getLogger("DeepGuard.Evaluation")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def evaluate_model_performance(
    model: tf.keras.Model,
    X_seq_test: np.ndarray,
    X_feat_test: np.ndarray,
    y_test: np.ndarray,
    data_source_tag: str = "synthetic_demo"
) -> Dict[str, Any]:
    """
    Evaluates model predictions against ground truth labels across multiple metrics.
    Finds optimal decision threshold maximizing F1-Score.

    Args:
        model (tf.keras.Model): Trained Keras fusion model.
        X_seq_test (np.ndarray): 3D sequence test tensor.
        X_feat_test (np.ndarray): 2D auxiliary feature test matrix.
        y_test (np.ndarray): Binary target ground truth test labels.
        data_source_tag (str): Data source identifier string.

    Returns:
        Dict[str, Any]: Comprehensive evaluation report dictionary.
    """
    logger.info(f"Evaluating Model Performance on {len(y_test)} Test Samples...")

    # Predict raw probabilities
    y_probs = model.predict([X_seq_test, X_feat_test], verbose=0).ravel()

    # 1. Standard Metrics @ Default Threshold = 0.5
    y_pred_default = (y_probs >= 0.5).astype(int)
    
    acc_default = accuracy_score(y_test, y_pred_default)
    prec_default = precision_score(y_test, y_pred_default, zero_division=0)
    rec_default = recall_score(y_test, y_pred_default, zero_division=0)
    f1_default = f1_score(y_test, y_pred_default, zero_division=0)

    # 2. Advanced Imbalanced Metrics (ROC-AUC & PR-AUC)
    try:
        roc_auc = roc_auc_score(y_test, y_probs)
    except ValueError:
        roc_auc = 0.5

    precision_curve, recall_curve, thresholds_pr = precision_recall_curve(y_test, y_probs)
    pr_auc = auc(recall_curve, precision_curve)

    # 3. Find Optimal Decision Threshold (Maximizing F1-Score)
    best_threshold = 0.5
    best_f1 = 0.0
    
    threshold_grid = np.linspace(0.1, 0.9, 81)
    for thresh in threshold_grid:
        y_pred_t = (y_probs >= thresh).astype(int)
        f1_t = f1_score(y_test, y_pred_t, zero_division=0)
        if f1_t > best_f1:
            best_f1 = f1_t
            best_threshold = float(thresh)

    # Optimal Threshold Predictions & Confusion Matrix
    y_pred_opt = (y_probs >= best_threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred_opt)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (int(cm[0, 0]), 0, 0, 0)

    prec_opt = precision_score(y_test, y_pred_opt, zero_division=0)
    rec_opt = recall_score(y_test, y_pred_opt, zero_division=0)

    eval_report = {
        "data_source_tag": data_source_tag,
        "num_test_samples": len(y_test),
        "test_theft_count": int(np.sum(y_test == 1)),
        "test_normal_count": int(np.sum(y_test == 0)),
        "metrics_at_default_0.5_threshold": {
            "accuracy": float(acc_default),
            "precision": float(prec_default),
            "recall": float(rec_default),
            "f1_score": float(f1_default)
        },
        "overall_curves": {
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc)
        },
        "optimal_threshold_tuning": {
            "optimal_threshold": best_threshold,
            "optimal_f1_score": float(best_f1),
            "precision_at_optimal": float(prec_opt),
            "recall_at_optimal": float(rec_opt)
        },
        "confusion_matrix_at_optimal": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        }
    }

    # Print Formatted Evaluation Report
    print("\n" + "=" * 65)
    print(f"         DEEPGUARD HYBRID MODEL EVALUATION REPORT        ")
    print("=" * 65)
    print(f" Data Source                : {data_source_tag}")
    print(f" Test Set Size              : {len(y_test)} samples")
    print(f" Area Under ROC Curve       : {roc_auc:.4f}")
    print(f" Area Under PR Curve        : {pr_auc:.4f}")
    print("-" * 65)
    print(f" Default Threshold (0.50)   : F1={f1_default:.4f} | Prec={prec_default:.4f} | Rec={rec_default:.4f}")
    print(f" Optimal Decision Threshold : {best_threshold:.2f}")
    print(f" Metrics @ Optimal Thresh   : F1={best_f1:.4f} | Prec={prec_opt:.4f} | Rec={rec_opt:.4f}")
    print("-" * 65)
    print(f" Confusion Matrix @ {best_threshold:.2f}    : TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print("=" * 65 + "\n")

    # Save Evaluation Report JSON
    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"eval_{data_source_tag}_{MODEL_VERSION}.json"
    report_path = str(logs_dir / report_filename)

    with open(report_path, "w") as f:
        json.dump(eval_report, f, indent=2)

    logger.info(f"Saved evaluation report to: {report_path}")
    return eval_report


def run_evaluation_pipeline(
    checkpoint_path: Optional[str] = None,
    csv_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Loads test split data and saved checkpoint to execute evaluation pipeline.
    """
    splits, quality_report, data_source_tag = load_training_data(csv_file_path)

    from ml.models.transformer_model import SinusoidalPositionalEncoding

    if checkpoint_path is None:
        checkpoint_path = str(ARTIFACTS_DIR / "checkpoints" / f"{data_source_tag}_fusion_{MODEL_VERSION}.keras")

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Saved model checkpoint not found at: {checkpoint_path}")

    logger.info(f"Loading trained Keras model from: {checkpoint_path}")
    model = tf.keras.models.load_model(
        checkpoint_path,
        custom_objects={"SinusoidalPositionalEncoding": SinusoidalPositionalEncoding}
    )

    X_seq_test = splits["test"]["X_seq"]
    X_feat_test = splits["test"]["X_feat"]
    y_test = splits["test"]["y"]

    return evaluate_model_performance(model, X_seq_test, X_feat_test, y_test, data_source_tag)


if __name__ == "__main__":
    run_evaluation_pipeline()
