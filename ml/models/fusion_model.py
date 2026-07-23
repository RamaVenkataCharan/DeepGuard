"""
Fusion Model Component for DeepGuard.
Combines Bi-LSTM and Transformer branches into an ensemble classifier.
"""
import tensorflow as tf
from tensorflow.keras import layers, Model
from ml.config import FUSION_DENSE_UNITS, FUSION_DROPOUT, FUSION_METHOD, LEARNING_RATE
from ml.models.bilstm_model import build_bilstm_branch
from ml.models.transformer_model import build_transformer_branch

def build_fusion_model(input_shape):
    """
    Builds the combined Bi-LSTM + Transformer fusion model.
    
    Args:
        input_shape: tuple of (sequence_length, num_features)
        
    Returns:
        Compiled Keras Model representing the fusion system.
    """
    inputs = layers.Input(shape=input_shape, name="sequence_input")
    
    # Instantiate branches
    bilstm_branch = build_bilstm_branch(input_shape)
    transformer_branch = build_transformer_branch(input_shape)
    
    # Extract features from both branches using the same input
    bilstm_feats = bilstm_branch(inputs)
    transformer_feats = transformer_branch(inputs)
    
    # Fusion mechanism
    if FUSION_METHOD == "concatenate":
        fused = layers.Concatenate(name="fusion_concat")([bilstm_feats, transformer_feats])
    elif FUSION_METHOD == "weighted_average":
        # Learnable weights for combination
        # Simplified as simple average for now
        fused = layers.Average(name="fusion_average")([bilstm_feats, transformer_feats])
    else:
        # Default to concatenation
        fused = layers.Concatenate(name="fusion_concat")([bilstm_feats, transformer_feats])
        
    # Dense classification block
    x = fused
    for i, units in enumerate(FUSION_DENSE_UNITS):
        x = layers.Dense(units, activation="relu", name=f"fusion_dense_{i+1}")(x)
        x = layers.BatchNormalization(name=f"fusion_bn_{i+1}")(x)
        x = layers.Dropout(FUSION_DROPOUT, name=f"fusion_dropout_{i+1}")(x)
        
    # Final classification output
    outputs = layers.Dense(1, activation="sigmoid", name="theft_probability")(x)
    
    # Build complete model
    model = Model(inputs=inputs, outputs=outputs, name="deepguard_fusion_model")
    
    # Compile model with standard metrics
    optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    model.compile(
        optimizer=optimizer,
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc", curve="PR")
        ]
    )
    
    return model
