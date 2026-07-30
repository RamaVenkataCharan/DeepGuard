"""
Bidirectional LSTM Model Component for DeepGuard.
Captures historical and bidirectional temporal consumption dependencies.
"""
import tensorflow as tf
from tensorflow.keras import layers, Model
from ml.config import BILSTM_UNITS_L1, BILSTM_UNITS_L2, BILSTM_DROPOUT, BILSTM_RECURRENT_DROPOUT

def build_bilstm_branch(input_shape=(14, 1)) -> Model:
    """
    Builds the Bi-LSTM feature extractor branch.

    Args:
        input_shape (tuple): Shape of raw 3D input sequence (sequence_length, num_features).

    Returns:
        tf.keras.Model: Feature extractor model outputting a 32-dimensional embedding vector.
    """
    inputs = layers.Input(shape=input_shape, name="bilstm_seq_input")
    
    # Layer 1: Bidirectional LSTM returning sequences (64 units)
    x = layers.Bidirectional(
        layers.LSTM(
            BILSTM_UNITS_L1,
            return_sequences=True,
            dropout=BILSTM_DROPOUT,
            recurrent_dropout=BILSTM_RECURRENT_DROPOUT
        ),
        name="bilstm_layer_1"
    )(inputs)
    x = layers.BatchNormalization(name="bilstm_bn_1")(x)
    
    # Layer 2: Bidirectional LSTM returning final state (32 units)
    x = layers.Bidirectional(
        layers.LSTM(
            BILSTM_UNITS_L2,
            return_sequences=False,
            dropout=BILSTM_DROPOUT,
            recurrent_dropout=BILSTM_RECURRENT_DROPOUT
        ),
        name="bilstm_layer_2"
    )(x)
    x = layers.BatchNormalization(name="bilstm_bn_2")(x)
    
    # Feature Embedding Output
    outputs = layers.Dense(32, activation="relu", name="bilstm_embeddings")(x)
    
    model = Model(inputs=inputs, outputs=outputs, name="bilstm_branch")
    return model
