"""
Transformer Model Component for DeepGuard.
Captures long-range dependencies, multi-head self-attention, and consumption volatility.
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
from ml.config import (
    TRANSFORMER_NUM_HEADS,
    TRANSFORMER_KEY_DIM,
    TRANSFORMER_FF_DIM,
    TRANSFORMER_NUM_BLOCKS,
    TRANSFORMER_DROPOUT,
    TRANSFORMER_EMBED_DIM
)

class SinusoidalPositionalEncoding(layers.Layer):
    """
    Sinusoidal Positional Encoding for time-series sequences.
    Uses static sin/cos functions (non-parametric) which excel on short sequences (14 steps)
    by preserving exact distance metrics without adding trainable parameters.
    """
    def __init__(self, sequence_length: int = 14, embed_dim: int = 32, **kwargs):
        super(SinusoidalPositionalEncoding, self).__init__(**kwargs)
        self.sequence_length = sequence_length
        self.embed_dim = embed_dim
        
        # Calculate static sinusoidal matrix
        position = np.arange(sequence_length)[:, np.newaxis]
        div_term = np.exp(np.arange(0, embed_dim, 2) * -(np.log(10000.0) / embed_dim))
        
        pe = np.zeros((sequence_length, embed_dim))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        self.positional_encoding = tf.cast(tf.constant(pe[np.newaxis, ...]), dtype=tf.float32)

    def call(self, inputs):
        return inputs + self.positional_encoding

    def get_config(self):
        config = super(SinusoidalPositionalEncoding, self).get_config()
        config.update({
            "sequence_length": self.sequence_length,
            "embed_dim": self.embed_dim,
        })
        return config


def transformer_encoder_block(inputs, embed_dim=32, num_heads=2, key_dim=16, ff_dim=64, dropout_rate=0.2):
    """
    Standard Transformer Encoder block with Multi-Head Self-Attention, LayerNorm, and Residuals.
    """
    # 1. Multi-Head Self-Attention
    attn_output = layers.MultiHeadAttention(
        num_heads=num_heads,
        key_dim=key_dim,
        dropout=dropout_rate,
        name="multi_head_attention"
    )(inputs, inputs)
    x1 = layers.Add(name="attn_residual")([inputs, attn_output])
    x1 = layers.LayerNormalization(epsilon=1e-6, name="attn_layernorm")(x1)
    
    # 2. Feed-Forward Network
    ffn_output = layers.Dense(ff_dim, activation="relu", name="ffn_dense_1")(x1)
    ffn_output = layers.Dense(embed_dim, name="ffn_dense_2")(ffn_output)
    ffn_output = layers.Dropout(dropout_rate, name="ffn_dropout")(ffn_output)
    x2 = layers.Add(name="ffn_residual")([x1, ffn_output])
    x2 = layers.LayerNormalization(epsilon=1e-6, name="ffn_layernorm")(x2)
    return x2


def build_transformer_branch(input_shape=(14, 1)) -> Model:
    """
    Builds the Transformer feature extractor branch.

    Args:
        input_shape (tuple): Shape of raw 3D input sequence (sequence_length, num_features).

    Returns:
        tf.keras.Model: Feature extractor model outputting a 32-dimensional embedding vector.
    """
    sequence_length, _ = input_shape
    inputs = layers.Input(shape=input_shape, name="transformer_seq_input")
    
    # Feature Projection to d_model (32)
    x = layers.Dense(TRANSFORMER_EMBED_DIM, activation="relu", name="input_projection")(inputs)
    
    # Sinusoidal Positional Encoding
    x = SinusoidalPositionalEncoding(sequence_length, TRANSFORMER_EMBED_DIM, name="sinusoidal_pe")(x)
    
    # Transformer Encoder Block(s)
    for i in range(TRANSFORMER_NUM_BLOCKS):
        x = transformer_encoder_block(
            x,
            embed_dim=TRANSFORMER_EMBED_DIM,
            num_heads=TRANSFORMER_NUM_HEADS,
            key_dim=TRANSFORMER_KEY_DIM,
            ff_dim=TRANSFORMER_FF_DIM,
            dropout_rate=TRANSFORMER_DROPOUT
        )
    
    # Temporal Aggregation
    x = layers.GlobalAveragePooling1D(name="global_avg_pool")(x)
    x = layers.Dropout(TRANSFORMER_DROPOUT, name="transformer_dropout")(x)
    
    outputs = layers.Dense(32, activation="relu", name="transformer_embeddings")(x)
    
    model = Model(inputs=inputs, outputs=outputs, name="transformer_branch")
    return model
