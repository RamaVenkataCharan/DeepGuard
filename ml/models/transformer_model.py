"""
Transformer Model Component for DeepGuard.
Captures long-range dependencies, periodicity, and attention-based patterns in consumption sequences.
"""
import tensorflow as tf
from tensorflow.keras import layers, Model
from ml.config import TRANSFORMER_NUM_HEADS, TRANSFORMER_FF_DIM, TRANSFORMER_NUM_BLOCKS, TRANSFORMER_DROPOUT, TRANSFORMER_EMBED_DIM

class PositionalEncoding(layers.Layer):
    """
    Learned positional embedding layer for 1D sequences.
    """
    def __init__(self, sequence_length, embed_dim, **kwargs):
        super(PositionalEncoding, self).__init__(**kwargs)
        self.sequence_length = sequence_length
        self.embed_dim = embed_dim
        self.pos_emb = layers.Embedding(input_dim=sequence_length, output_dim=embed_dim)

    def call(self, x):
        positions = tf.range(start=0, limit=self.sequence_length, delta=1)
        positions = self.pos_emb(positions)
        return x + positions

    def get_config(self):
        config = super(PositionalEncoding, self).get_config()
        config.update({
            "sequence_length": self.sequence_length,
            "embed_dim": self.embed_dim,
        })
        return config

def transformer_encoder_block(inputs, embed_dim, num_heads, ff_dim, dropout_rate):
    """
    Single Transformer Encoder block.
    """
    # Attention and Normalization
    attention_output = layers.MultiHeadAttention(
        num_heads=num_heads, key_dim=embed_dim, dropout=dropout_rate
    )(inputs, inputs)
    x1 = layers.Add()([inputs, attention_output])
    x1 = layers.LayerNormalization(epsilon=1e-6)(x1)
    
    # Feed Forward and Normalization
    ffn_output = layers.Dense(ff_dim, activation="relu")(x1)
    ffn_output = layers.Dense(embed_dim)(ffn_output)
    ffn_output = layers.Dropout(dropout_rate)(ffn_output)
    x2 = layers.Add()([x1, ffn_output])
    x2 = layers.LayerNormalization(epsilon=1e-6)(x2)
    return x2

def build_transformer_branch(input_shape):
    """
    Builds the Transformer feature extractor branch.
    
    Args:
        input_shape: tuple of (sequence_length, num_features)
        
    Returns:
        Keras Model representing the Transformer branch.
    """
    sequence_length = input_shape[0]
    num_features = input_shape[1]
    
    inputs = layers.Input(shape=input_shape, name="transformer_input")
    
    # Project features to embed dimension if different
    x = layers.Dense(TRANSFORMER_EMBED_DIM, activation="relu")(inputs)
    
    # Add Positional Encoding
    x = PositionalEncoding(sequence_length, TRANSFORMER_EMBED_DIM)(x)
    
    # Apply Transformer Encoder blocks
    for _ in range(TRANSFORMER_NUM_BLOCKS):
        x = transformer_encoder_block(
            x, 
            embed_dim=TRANSFORMER_EMBED_DIM, 
            num_heads=TRANSFORMER_NUM_HEADS, 
            ff_dim=TRANSFORMER_FF_DIM, 
            dropout_rate=TRANSFORMER_DROPOUT
        )
    
    # Global average pooling over the sequence dimension
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(TRANSFORMER_DROPOUT)(x)
    
    outputs = layers.Dense(64, activation="relu", name="transformer_features")(x)
    
    model = Model(inputs=inputs, outputs=outputs, name="transformer_branch")
    return model
