"""
Hyperparameter Tuning Module for DeepGuard.
Performs grid search / random search over key sequence lengths, learning rates, 
and branch configurations to discover the optimal model setup.
"""
import logging
import numpy as np
from ml.config import TUNING_PARAM_GRID, ARTIFACTS_DIR
from ml.data.loaders.sgcc_loader import load_sgcc_dataset
from ml.preprocessing.cleaning import clean_dataset
from ml.preprocessing.normalization import normalize_dataset
from ml.preprocessing.sequence_builder import build_dataset, split_dataset
from ml.models.fusion_model import build_fusion_model
import tensorflow as tf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def tune_hyperparameters():
    logger.info("Initializing Hyperparameter Tuning Process...")
    
    # Load dataset once
    df = load_sgcc_dataset()
    df_cleaned = clean_dataset(df)
    df_normalized, scaler = normalize_dataset(df_cleaned, fit=True)
    
    best_loss = float("inf")
    best_config = {}
    
    # Define a simplified search space for development speed
    sequence_lengths = [7, 14]
    learning_rates = [0.001, 0.0005]
    batch_sizes = [32, 64]
    
    results = []
    
    for seq_len in sequence_lengths:
        X, y, _ = build_dataset(
            df_normalized,
            sequence_length=seq_len,
            aggregate="all"
        )
        splits = split_dataset(X, y)
        X_train, y_train = splits["train"]
        X_val, y_val = splits["val"]
        
        for lr in learning_rates:
            for bs in batch_sizes:
                logger.info(f"Testing Config: seq_len={seq_len}, learning_rate={lr}, batch_size={bs}")
                
                # Build model dynamically
                input_shape = (seq_len, X.shape[2])
                model = build_fusion_model(input_shape)
                
                # Recompile with custom learning rate
                optimizer = tf.keras.optimizers.Adam(learning_rate=lr)
                model.compile(optimizer=optimizer, loss="binary_crossentropy", metrics=["accuracy"])
                
                # Run small fast training (e.g. 3 epochs) for demonstration
                history = model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=3,
                    batch_size=bs,
                    verbose=0
                )
                
                val_loss = min(history.history["val_loss"])
                logger.info(f"Validation Loss: {val_loss:.4f}")
                
                config = {
                    "sequence_length": seq_len,
                    "learning_rate": lr,
                    "batch_size": bs,
                    "val_loss": val_loss
                }
                results.append(config)
                
                if val_loss < best_loss:
                    best_loss = val_loss
                    best_config = config
                    
    logger.info("Hyperparameter Tuning Complete!")
    logger.info(f"Best Config Found: {best_config}")
    
    # Save tuning log
    import json
    with open(ARTIFACTS_DIR / "hyperparameter_tuning_results.json", "w") as f:
        json.dump({"best_config": best_config, "all_results": results}, f, indent=4)
        
if __name__ == "__main__":
    tune_hyperparameters()
