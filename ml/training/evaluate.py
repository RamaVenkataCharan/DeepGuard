"""
Model Evaluation Pipeline.
Loads trained model, predicts on the test set, computes performance metrics, and plots evaluation curves.
"""
import os
import logging
from pathlib import Path
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    f1_score
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from ml.config import ARTIFACTS_DIR, MODEL_FILENAME, DEFAULT_SEQUENCE_LENGTH
from ml.data.loaders.sgcc_loader import load_sgcc_dataset
from ml.preprocessing.cleaning import clean_dataset
from ml.preprocessing.normalization import normalize_dataset
from ml.preprocessing.sequence_builder import build_dataset, split_dataset

def evaluate_model():
    logger.info("Starting Model Evaluation Process...")
    
    # 1. Load test data
    df = load_sgcc_dataset()
    df_cleaned = clean_dataset(df)
    df_normalized, scaler = normalize_dataset(df_cleaned, fit=True)
    
    X, y, _ = build_dataset(
        df_normalized,
        sequence_length=DEFAULT_SEQUENCE_LENGTH,
        aggregate="all"
    )
    splits = split_dataset(X, y)
    X_test, y_test = splits["test"]
    
    # 2. Load model
    model_path = ARTIFACTS_DIR / MODEL_FILENAME
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Please run train.py first.")
        
    logger.info(f"Loading trained model from {model_path}...")
    model = tf.keras.models.load_model(str(model_path), custom_objects={"PositionalEncoding": None}) # Keras auto-loads custom classes if registered or using default deserialization
    
    # 3. Generate Predictions
    y_pred_prob = model.predict(X_test, verbose=0).ravel()
    y_pred = (y_pred_prob >= 0.5).astype(int)
    
    # 4. Calculate Metrics
    auc_score = roc_auc_score(y_test, y_pred_prob)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=False)
    
    logger.info("Evaluation Complete. Performance Summary:")
    logger.info(f"ROC-AUC Score: {auc_score:.4f}")
    logger.info(f"F1-Score (Theft class): {f1:.4f}")
    logger.info(f"Confusion Matrix:\n{cm}")
    logger.info(f"Classification Report:\n{report}")
    
    # Save Report to File
    with open(ARTIFACTS_DIR / "evaluation_report.txt", "w") as f:
        f.write(f"DeepGuard Model Evaluation Report\n")
        f.write(f"==================================\n")
        f.write(f"ROC-AUC: {auc_score:.4f}\n")
        f.write(f"F1-Score: {f1:.4f}\n\n")
        f.write("Confusion Matrix:\n")
        f.write(f"{cm}\n\n")
        f.write("Classification Report:\n")
        f.write(report)
        
    # 5. Plot curves
    plot_evaluation_charts(y_test, y_pred_prob, cm)
    
    logger.info(f"Charts saved to {ARTIFACTS_DIR}")

def plot_evaluation_charts(y_true, y_prob, cm):
    # Setup plotting directory
    fig_dir = ARTIFACTS_DIR / "plots"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Normal", "Theft"], yticklabels=["Normal", "Theft"])
    plt.title("Confusion Matrix")
    plt.ylabel("Actual Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    plt.savefig(fig_dir / "confusion_matrix.png", dpi=150)
    plt.close()
    
    # Plot ROC Curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (area = {roc_auc_score(y_true, y_prob):.2f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic (ROC)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(fig_dir / "roc_curve.png", dpi=150)
    plt.close()
    
    # Plot PR Curve
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, color="blue", lw=2, label="Precision-Recall curve")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall (PR) Curve")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.tight_layout()
    plt.savefig(fig_dir / "pr_curve.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    evaluate_model()
