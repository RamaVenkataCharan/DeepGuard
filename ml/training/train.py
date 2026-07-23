"""
End-to-end Model Training Pipeline.
Loads data, preprocesses, splits, trains the Fusion model, and saves artifacts.
"""
import os
import logging
from pathlib import Path
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from ml.config import (
    DEFAULT_SEQUENCE_LENGTH,
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    EARLY_STOPPING_PATIENCE,
    LR_REDUCTION_PATIENCE,
    LR_REDUCTION_FACTOR,
    MIN_LEARNING_RATE,
    MODEL_FILENAME,
    ARTIFACTS_DIR
)
from ml.data.loaders.sgcc_loader import load_sgcc_dataset
from ml.preprocessing.cleaning import clean_dataset
from ml.preprocessing.normalization import normalize_dataset
from ml.preprocessing.sequence_builder import build_dataset, split_dataset
from ml.models.fusion_model import build_fusion_model

def run_training():
    logger.info("Starting DeepGuard Model Training Pipeline...")
    
    # 1. Load Dataset
    df = load_sgcc_dataset()
    
    # 2. Clean Dataset
    df_cleaned = clean_dataset(df)
    
    # 3. Normalize Dataset
    df_normalized, scaler = normalize_dataset(df_cleaned, fit=True)
    
    # Save Scaler artifact
    scaler_path = scaler.save()
    logger.info(f"Scaler saved to {scaler_path}")
    
    # 4. Build Sequence Dataset (using last sliding window for prediction, or all window splits for training)
    # For training we use all windows to increase sample size
    X, y, cids = build_dataset(
        df_normalized,
        sequence_length=DEFAULT_SEQUENCE_LENGTH,
        aggregate="all"
    )
    
    # 5. Split Dataset
    splits = split_dataset(X, y)
    X_train, y_train = splits["train"]
    X_val, y_val = splits["val"]
    X_test, y_test = splits["test"]
    
    # 6. Compute Class Weights for Imbalance
    classes = np.unique(y_train)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train
    )
    class_weights = dict(zip(classes, weights))
    logger.info(f"Computed Class Weights: {class_weights}")
    
    # 7. Build Model
    input_shape = (DEFAULT_SEQUENCE_LENGTH, X.shape[2])
    logger.info(f"Input Shape: {input_shape}")
    model = build_fusion_model(input_shape)
    model.summary(print_fn=logger.info)
    
    # 8. Define Callbacks
    checkpoint_path = ARTIFACTS_DIR / MODEL_FILENAME
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=LR_REDUCTION_FACTOR,
            patience=LR_REDUCTION_PATIENCE,
            min_lr=MIN_LEARNING_RATE,
            verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path),
            monitor="val_loss",
            save_best_only=True,
            verbose=1
        )
    ]
    
    # 9. Train Model
    logger.info("Beginning model fitting...")
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1
    )
    
    logger.info(f"Training completed. Model saved to {checkpoint_path}")
    return model, history, splits

if __name__ == "__main__":
    run_training()
