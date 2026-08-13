"""
DeepGuard — Empirical Probability Swing Diagnostic Script
===========================================================
Trains 2 epochs with seed=123, capturing the exact predicted probability distributions
at the end of Epoch 1 and Epoch 2 to prove the recall collapse mechanism.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["KERAS_BACKEND"] = "tensorflow"  # Use baseline Keras/TF

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
logger = logging.getLogger("DeepGuard.ProbDiag")

class ProbabilityDistributionCallback(keras.callbacks.Callback):
    def __init__(self, val_data):
        super().__init__()
        self.val_x, self.val_y = val_data
        self.epoch_probs = {}

    def on_epoch_end(self, epoch, logs=None):
        preds = self.model.predict(self.val_x, batch_size=8192, verbose=0).flatten()
        percentiles = np.percentile(preds, [0, 10, 25, 50, 75, 90, 99, 100])
        above_05 = (preds >= 0.5).mean()
        self.epoch_probs[epoch + 1] = {
            "min": float(percentiles[0]),
            "p10": float(percentiles[1]),
            "p25": float(percentiles[2]),
            "p50": float(percentiles[3]),
            "p75": float(percentiles[4]),
            "p90": float(percentiles[5]),
            "p99": float(percentiles[6]),
            "max": float(percentiles[7]),
            "mean": float(preds.mean()),
            "std": float(preds.std()),
            "fraction_positive_predicted": float(above_05)
        }
        print(f"\n--- END OF EPOCH {epoch + 1} PROBABILITY DISTRIBUTION (val_size={len(preds)}) ---")
        print(f"  Min   : {percentiles[0]:.6f}")
        print(f"  P25   : {percentiles[2]:.6f}")
        print(f"  Median: {percentiles[3]:.6f}")
        print(f"  P75   : {percentiles[4]:.6f}")
        print(f"  Max   : {percentiles[7]:.6f}")
        print(f"  Mean  : {preds.mean():.6f}")
        print(f"  Fraction >= 0.5 (Predicted Theft): {above_05*100:.2f}% (True Theft Ratio: {self.val_y.mean()*100:.2f}%)")

def main():
    SGCC_DATA_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "data.csv")
    splits, quality_report = run_preprocessing_pipeline(SGCC_DATA_PATH, apply_smote_on_features=False)

    SEED = 123
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
    keras.utils.set_random_seed(SEED)

    model = build_hybrid_fusion_model(
        seq_shape=(14, 1),
        feat_shape=(8,),
        learning_rate=1e-3
    )

    prob_cb = ProbabilityDistributionCallback(([X_seq_val, X_feat_val], y_val))

    history = model.fit(
        x=[X_seq_train, X_feat_train],
        y=y_train,
        validation_data=([X_seq_val, X_feat_val], y_val),
        epochs=2,
        batch_size=8192,
        class_weight=class_weights,
        callbacks=[prob_cb],
        verbose=1
    )

    out_file = ARTIFACTS_DIR / "logs" / "probability_swing_diagnostic.json"
    with open(out_file, "w") as f:
        json.dump(prob_cb.epoch_probs, f, indent=2)

if __name__ == "__main__":
    main()
