"""
DeepGuard — Stabilized Baseline Training Run
=============================================
Applies 3 targeted hyperparameter fixes to resolve training instability:
1. Lower Learning Rate: 1e-4 (10x reduction from 1e-3)
2. Square-Root Dampened Class Weights: {0: 0.739349, 1: 2.420864} (ratio 3.27x instead of 10.72x)
3. Gradient Clipping: clipnorm=1.0
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

from ml.config import ARTIFACTS_DIR
from ml.preprocessing.preprocess import run_preprocessing_pipeline
from ml.models.fusion_model import build_hybrid_fusion_model

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DeepGuard.StabilizedBaseline")

class ProbabilityDistributionCallback(keras.callbacks.Callback):
    def __init__(self, val_data):
        super().__init__()
        self.val_x, self.val_y = val_data
        self.epoch_probs = {}

    def on_epoch_end(self, epoch, logs=None):
        preds = self.model.predict(self.val_x, batch_size=8192, verbose=0).flatten()
        percentiles = np.percentile(preds, [0, 10, 25, 50, 75, 90, 99, 100])
        above_05 = (preds >= 0.5).mean()
        self.epoch_probs[str(epoch + 1)] = {
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
        print(f"\n--- STABILIZED EPOCH {epoch + 1} PROBABILITY DISTRIBUTION (val_size={len(preds)}) ---")
        print(f"  Min   : {percentiles[0]:.6f}")
        print(f"  P25   : {percentiles[2]:.6f}")
        print(f"  Median: {percentiles[3]:.6f}")
        print(f"  P75   : {percentiles[4]:.6f}")
        print(f"  Max   : {percentiles[7]:.6f}")
        print(f"  Mean  : {preds.mean():.6f}")
        print(f"  Std   : {preds.std():.6f}")
        print(f"  Fraction >= 0.5 (Predicted Theft): {above_05*100:.2f}% (True Theft Ratio: {self.val_y.mean()*100:.2f}%)")

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

    # FIX 2: Square-root dampened class weights
    raw_weights = quality_report.get("loss_class_weights", {0: 0.5466367, 1: 5.8605809})
    w0_damp = float(np.sqrt(raw_weights[0]))
    w1_damp = float(np.sqrt(raw_weights[1]))
    dampened_class_weights = {0: w0_damp, 1: w1_damp}

    # FIX 1 & FIX 3: Lower LR (1e-4) and clipnorm=1.0
    STABILIZED_LR = 1e-4
    CLIPNORM = 1.0

    logger.info(f"STABILIZED BASELINE RUN: Seed={SEED}, Train={len(y_train):,}, Val={len(y_val):,}, BatchSize=8192")
    logger.info(f"Raw Class Weights: {raw_weights}")
    logger.info(f"Dampened Class Weights (sqrt ratio): {dampened_class_weights}")
    logger.info(f"Stabilized Learning Rate: {STABILIZED_LR}")
    logger.info(f"Gradient Clipping (clipnorm): {CLIPNORM}")

    keras.utils.set_random_seed(SEED)

    model = build_hybrid_fusion_model(
        seq_shape=(14, 1),
        feat_shape=(8,),
        learning_rate=STABILIZED_LR,
        clipnorm=CLIPNORM
    )

    prob_cb = ProbabilityDistributionCallback(([X_seq_val, X_feat_val], y_val))

    t0 = time.time()
    history = model.fit(
        x=[X_seq_train, X_feat_train],
        y=y_train,
        validation_data=([X_seq_val, X_feat_val], y_val),
        epochs=2,
        batch_size=8192,
        class_weight=dampened_class_weights,
        callbacks=[prob_cb],
        verbose=1
    )
    t1 = time.time()
    total_time = t1 - t0
    logger.info(f"Stabilized baseline run completed in {total_time:.2f} seconds ({total_time/2:.2f} s/epoch)")

    # Save metrics history
    hist_dict = {k: [float(x) for x in v] for k, v in history.history.items()}
    hist_dict["measured_total_seconds"] = float(total_time)
    hist_dict["measured_seconds_per_epoch"] = float(total_time / 2.0)
    hist_dict["seed"] = SEED
    hist_dict["batch_size"] = 8192
    hist_dict["learning_rate"] = STABILIZED_LR
    hist_dict["clipnorm"] = CLIPNORM
    hist_dict["class_weights"] = dampened_class_weights

    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out_file = logs_dir / "stabilized_baseline_history.json"
    with open(out_file, "w") as f:
        json.dump(hist_dict, f, indent=2)

    # Save probability distribution
    prob_out_file = logs_dir / "stabilized_probability_distribution.json"
    with open(prob_out_file, "w") as f:
        json.dump(prob_cb.epoch_probs, f, indent=2)

    print("\n" + "="*75)
    print(f"  STABILIZED BASELINE RESULTS (SEED={SEED}, BATCH_SIZE=8192, LR=1e-4, CLIPNORM=1.0)")
    print("="*75)
    for ep in range(2):
        print(f"\n--- EPOCH {ep+1} ---")
        for k in sorted(history.history.keys()):
            val = history.history[k][ep]
            print(f"  {k:20s}: {val:.6f}")
    print("="*75 + "\n")

if __name__ == "__main__":
    main()
