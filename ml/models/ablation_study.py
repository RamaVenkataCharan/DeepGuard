"""
DeepGuard Model Ablation Study & Leakage-Free Evaluation Pipeline
==================================================================
Performs rigorous ablation comparison across three architectures:
1. Hybrid Fusion Model (Bi-LSTM + Transformer + Auxiliary Feature Branch)
2. Bi-LSTM Standalone Model
3. Transformer Standalone Model

Leakage-Free Protocol:
- Decision threshold selection is performed STRICTLY on the VALIDATION SET.
- The validation-selected threshold (tau_val) is applied ONCE to the TEST SET.
- Synthetic dataset disclaimers and test customer count sample size warnings are embedded.

Author: Senior ML Engineer (DeepGuard Project)
"""

import os
import json
import logging
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, confusion_matrix
)

from ml.config import ARTIFACTS_DIR, LEARNING_RATE, BATCH_SIZE, EPOCHS, EARLY_STOPPING_PATIENCE
from ml.models.train import load_training_data
from ml.models.bilstm_model import build_bilstm_branch
from ml.models.transformer_model import build_transformer_branch, SinusoidalPositionalEncoding
from ml.models.fusion_model import build_hybrid_fusion_model

logger = logging.getLogger("DeepGuard.Ablation")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def build_bilstm_standalone(seq_shape=(14, 1), learning_rate: float = LEARNING_RATE) -> Model:
    """Builds a standalone Bi-LSTM classification model."""
    inputs = layers.Input(shape=seq_shape, name="sequence_input")
    bilstm_emb = build_bilstm_branch(seq_shape)(inputs)
    x = layers.Dense(16, activation="relu")(bilstm_emb)
    outputs = layers.Dense(1, activation="sigmoid", name="theft_probability")(x)
    
    model = Model(inputs=inputs, outputs=outputs, name="bilstm_standalone")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc_pr", curve="PR")]
    )
    return model


def build_transformer_standalone(seq_shape=(14, 1), learning_rate: float = LEARNING_RATE) -> Model:
    """Builds a standalone Transformer classification model."""
    inputs = layers.Input(shape=seq_shape, name="sequence_input")
    trans_emb = build_transformer_branch(seq_shape)(inputs)
    x = layers.Dense(16, activation="relu")(trans_emb)
    outputs = layers.Dense(1, activation="sigmoid", name="theft_probability")(x)
    
    model = Model(inputs=inputs, outputs=outputs, name="transformer_standalone")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc_pr", curve="PR")]
    )
    return model


def train_and_evaluate_leakage_free(
    model_name: str,
    model: Model,
    splits: dict,
    class_weights: dict,
    epochs: int = 50
) -> dict:
    """
    Trains model and performs LEAKAGE-FREE evaluation:
    1. Decision threshold is selected on VALIDATION split only.
    2. Selected threshold is applied ONCE to the TEST split.
    """
    logger.info(f"--- Training & Evaluating Variant: {model_name} ---")
    
    X_seq_tr = splits["train"]["X_seq"]
    X_feat_tr = splits["train"]["X_feat"]
    y_tr = splits["train"]["y"]

    X_seq_val = splits["val"]["X_seq"]
    X_feat_val = splits["val"]["X_feat"]
    y_val = splits["val"]["y"]

    X_seq_te = splits["test"]["X_seq"]
    X_feat_te = splits["test"]["X_feat"]
    y_te = splits["test"]["y"]

    # Determine inputs format (Hybrid accepts [seq, feat], standalone accepts [seq])
    is_hybrid = isinstance(model.input, list) and len(model.input) == 2
    tr_inputs = [X_seq_tr, X_feat_tr] if is_hybrid else X_seq_tr
    val_inputs = [X_seq_val, X_feat_val] if is_hybrid else X_seq_val
    te_inputs = [X_seq_te, X_feat_te] if is_hybrid else X_seq_te

    # Fit model with EarlyStopping on val_auc_pr
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_auc_pr",
            mode="max",
            patience=10,
            restore_best_weights=True,
            verbose=0
        )
    ]

    batch_sz = max(8, min(32, len(y_tr) // 4)) if len(y_tr) < 1000 else 32
    model.fit(
        x=tr_inputs,
        y=y_tr,
        validation_data=(val_inputs, y_val),
        epochs=epochs,
        batch_size=batch_sz,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=0
    )

    # ------------------------------------------------------------------------
    # STEP 1: THRESHOLD SELECTION ON VALIDATION SET ONLY (NO TEST LEAKAGE)
    # ------------------------------------------------------------------------
    val_probs = model.predict(val_inputs, verbose=0).ravel()
    best_tau_val = 0.5
    best_val_f1 = 0.0

    threshold_grid = np.linspace(0.10, 0.90, 81)
    for tau in threshold_grid:
        val_pred_tau = (val_probs >= tau).astype(int)
        f1_v = f1_score(y_val, val_pred_tau, zero_division=0)
        if f1_v > best_val_f1:
            best_val_f1 = f1_v
            best_tau_val = float(tau)

    # Calculate Val Metrics at tau_val
    val_pred_opt = (val_probs >= best_tau_val).astype(int)
    val_prec = precision_score(y_val, val_pred_opt, zero_division=0)
    val_rec = recall_score(y_val, val_pred_opt, zero_division=0)

    # ------------------------------------------------------------------------
    # STEP 2: APPLY tau_val ONCE TO UNSEEN TEST SET (UNBIASED TEST EVALUATION)
    # ------------------------------------------------------------------------
    test_probs = model.predict(te_inputs, verbose=0).ravel()
    test_pred_opt = (test_probs >= best_tau_val).astype(int)

    test_acc = accuracy_score(y_te, test_pred_opt)
    test_prec = precision_score(y_te, test_pred_opt, zero_division=0)
    test_rec = recall_score(y_te, test_pred_opt, zero_division=0)
    test_f1 = f1_score(y_te, test_pred_opt, zero_division=0)

    try:
        test_roc_auc = roc_auc_score(y_te, test_probs)
    except ValueError:
        test_roc_auc = 0.5

    p_curve, r_curve, _ = precision_recall_curve(y_te, test_probs)
    test_pr_auc = auc(r_curve, p_curve)

    cm = confusion_matrix(y_te, test_pred_opt)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (int(cm[0, 0]), 0, 0, 0)

    return {
        "model_name": model_name,
        "num_params": model.count_params(),
        "val_selected_threshold": best_tau_val,
        "val_justification": {
            "val_f1": float(best_val_f1),
            "val_precision": float(val_prec),
            "val_recall": float(val_rec)
        },
        "unbiased_test_results": {
            "test_f1": float(test_f1),
            "test_precision": float(test_prec),
            "test_recall": float(test_rec),
            "test_accuracy": float(test_acc),
            "test_roc_auc": float(test_roc_auc),
            "test_pr_auc": float(test_pr_auc),
            "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}
        }
    }


def run_ablation_study(csv_file_path: str = None) -> dict:
    """Executes the comparative ablation study across all 3 model variants."""
    logger.info("=== STARTING DEEPGUARD ABLATION STUDY ===")
    
    splits, quality_report, data_source_tag = load_training_data(csv_file_path)
    class_weights = quality_report.get("loss_class_weights", {0: 1.0, 1: 5.0})
    
    num_test_custs = splits["test"]["num_customers"]
    num_test_windows = splits["test"]["num_windows"]

    seq_shape = (splits["train"]["X_seq"].shape[1], splits["train"]["X_seq"].shape[2])
    feat_shape = (splits["train"]["X_feat"].shape[1],)

    # Instantiate Models
    models_to_test = {
        "Hybrid Fusion (Bi-LSTM + Trans + Aux)": build_hybrid_fusion_model(seq_shape, feat_shape),
        "Bi-LSTM Standalone": build_bilstm_standalone(seq_shape),
        "Transformer Standalone": build_transformer_standalone(seq_shape)
    }

    results = []
    for name, model_inst in models_to_test.items():
        res = train_and_evaluate_leakage_free(
            model_name=name,
            model=model_inst,
            splits=splits,
            class_weights=class_weights,
            epochs=50
        )
        results.append(res)

    # Create Final Summary Package
    ablation_report = {
        "data_source_tag": data_source_tag,
        "sample_size_warnings": {
            "synthetic_disclaimer": "WARNING: Evaluated on synthetic mock dataset. Results demonstrate pipeline correctness only, not production theft detection accuracy.",
            "unreliable_sample_size_warning": f"WARNING: Unreliable sample size (N_test_customers = {num_test_custs}, N_test_windows = {num_test_windows}). Metrics are subject to high variance."
        },
        "evaluation_protocol": "LEAKAGE-FREE: Threshold selected on validation split, applied once to unseen test split.",
        "ablation_results": results
    }

    # Print Console Summary Table
    print("\n" + "=" * 105)
    print("                     DEEPGUARD ABLATION STUDY COMPARISON TABLE                     ")
    print("=" * 105)
    header = f"| {'Model Variant':38s} | {'Params':7s} | {'Val tau':7s} | {'Val F1':6s} | {'Test PR-AUC':11s} | {'Test ROC':8s} | {'Test F1':7s} | {'CM (TN,FP,FN,TP)':16s} |"
    print(header)
    print("-" * 105)
    
    for r in results:
        m_name = r["model_name"]
        params = f"{r['num_params']:,}"
        tau = f"{r['val_selected_threshold']:.2f}"
        val_f1 = f"{r['val_justification']['val_f1']:.4f}"
        pr_auc = f"{r['unbiased_test_results']['test_pr_auc']:.4f}"
        roc_auc = f"{r['unbiased_test_results']['test_roc_auc']:.4f}"
        t_f1 = f"{r['unbiased_test_results']['test_f1']:.4f}"
        cm = r['unbiased_test_results']['confusion_matrix']
        cm_str = f"({cm['TN']},{cm['FP']},{cm['FN']},{cm['TP']})"
        
        print(f"| {m_name:38s} | {params:7s} | {tau:6s} | {val_f1:6s} | {pr_auc:11s} | {roc_auc:8s} | {t_f1:7s} | {cm_str:16s} |")
    print("=" * 105)

    print("\n" + report_disclaimer(num_test_custs, num_test_windows))

    # Save JSON Report
    logs_dir = ARTIFACTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out_path = logs_dir / f"ablation_study_{data_source_tag}.json"
    with open(out_path, "w") as f:
        json.dump(ablation_report, f, indent=2)

    logger.info(f"Ablation study completed. Saved report to: {out_path}")
    return ablation_report


def report_disclaimer(n_custs: int, n_wins: int) -> str:
    return (
        f"[SYSTEM DISCLAIMER & METHODOLOGY AUDIT]\n"
        f" 1. DATA SOURCE: Synthetic mock generator (50 customers, 30 days).\n"
        f"    Results demonstrate execution flow and leakage-free validation only.\n"
        f" 2. SAMPLE SIZE UNRELIABILITY: Measured on N_test_customers = {n_custs} ({n_wins} windows).\n"
        f"    Metrics are subject to high variance and are NOT representative of production benchmarks.\n"
        f" 3. LEAKAGE-FREE PROTOCOL: Threshold tau* was selected strictly on the VALIDATION split\n"
        f"    and applied once to the unseen TEST split."
    )


if __name__ == "__main__":
    run_ablation_study()
