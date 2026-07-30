"""
DeepGuard Fusion Architecture Component.
Combines Bi-LSTM, Transformer, and Auxiliary Statistical Feature branches into a late-fusion ensemble.
"""
import tensorflow as tf
from tensorflow.keras import layers, Model
from ml.config import LEARNING_RATE, FUSION_DROPOUT
from ml.models.bilstm_model import build_bilstm_branch
from ml.models.transformer_model import build_transformer_branch


def build_auxiliary_branch(input_shape=(8,)) -> Model:
    """
    Builds the auxiliary statistical feature sub-network.

    Args:
        input_shape (tuple): Shape of extracted statistical feature vector (8,).

    Returns:
        tf.keras.Model: Feature extractor outputting a 16-dimensional feature representation.
    """
    inputs = layers.Input(shape=input_shape, name="aux_feat_input")
    x = layers.Dense(16, activation="relu", name="aux_dense_1")(inputs)
    x = layers.BatchNormalization(name="aux_bn_1")(x)
    x = layers.Dropout(0.2, name="aux_dropout_1")(x)
    outputs = layers.Dense(16, activation="relu", name="aux_embeddings")(x)
    return Model(inputs=inputs, outputs=outputs, name="auxiliary_branch")


def build_hybrid_fusion_model(
    seq_shape=(14, 1),
    feat_shape=(8,),
    learning_rate: float = LEARNING_RATE
) -> Model:
    """
    Builds the complete DeepGuard Hybrid Dual-Branch + Auxiliary Fusion Classifier.

    Architecture Design (Late Fusion):
    - Branch 1: Bi-LSTM (Input: 14x1 sequence) -> 32d embedding
    - Branch 2: Transformer (Input: 14x1 sequence) -> 32d embedding
    - Branch 3: Auxiliary Feature Network (Input: 8d vector) -> 16d embedding
    - Fusion: Concatenation (80d joint embedding space)
    - Classification Head: Dense(32) -> BN -> Dropout(0.3) -> Dense(16) -> Sigmoid(1)

    Why Late Fusion Concatenation over Probability Averaging:
    Probability averaging assumes independent branch errors. Late fusion concatenation
    preserves joint cross-branch feature interactions (e.g. cross-correlating a Transformer
    attention spike with Bi-LSTM temporal variance and auxiliary kurtosis), drastically
    reducing false positive theft alarms.

    Args:
        seq_shape (tuple): Shape of raw 3D input sequence (14, 1).
        feat_shape (tuple): Shape of 2D statistical feature vector (8,).
        learning_rate (float): Adam optimizer learning rate.

    Returns:
        tf.keras.Model: Compiled Keras hybrid fusion model.
    """
    # Define Inputs
    seq_input = layers.Input(shape=seq_shape, name="sequence_input")
    feat_input = layers.Input(shape=feat_shape, name="feature_input")

    # Instantiate Branches
    bilstm_branch = build_bilstm_branch(seq_shape)
    transformer_branch = build_transformer_branch(seq_shape)
    aux_branch = build_auxiliary_branch(feat_shape)

    # Extract Branch Embeddings
    bilstm_emb = bilstm_branch(seq_input)
    transformer_emb = transformer_branch(seq_input)
    aux_emb = aux_branch(feat_input)

    # Late Fusion Concatenation (32 + 32 + 16 = 80d)
    fused = layers.Concatenate(name="late_fusion_concat")([bilstm_emb, transformer_emb, aux_emb])

    # Classification Head
    x = layers.Dense(32, activation="relu", name="fusion_dense_1")(fused)
    x = layers.BatchNormalization(name="fusion_bn_1")(x)
    x = layers.Dropout(FUSION_DROPOUT, name="fusion_dropout_1")(x)
    
    x = layers.Dense(16, activation="relu", name="fusion_dense_2")(x)
    x = layers.BatchNormalization(name="fusion_bn_2")(x)

    # Sigmoid Output Head
    outputs = layers.Dense(1, activation="sigmoid", name="theft_probability")(x)

    # Compile Hybrid Model
    model = Model(inputs=[seq_input, feat_input], outputs=outputs, name="deepguard_hybrid_fusion")
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc_pr", curve="PR"),
            tf.keras.metrics.AUC(name="auc_roc", curve="ROC")
        ]
    )

    return model

# Alias for backwards compatibility
build_fusion_model = build_hybrid_fusion_model

