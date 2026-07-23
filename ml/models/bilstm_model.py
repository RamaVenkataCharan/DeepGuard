"""
Bidirectional LSTM Model Component for DeepGuard.
Captures short-to-medium-term temporal dependencies in consumption sequences.
"""
import tensorflow as tf
from tensorflow.keras import layers, Model
from ml.config import BILSTM_UNITS_L1, BILSTM_UNITS_L2, BILSTM_DROPOUT, BILSTM_RECURRENT_DROPOUT

def build_bilstm_branch(input_shape):
    """
    Builds the Bi-LSTM feature extractor branch.
    
    Args:
        input_shape: tuple of (sequence_length, num_features)
        
    Returns:
        Keras Model representing the Bi-LSTM branch.
    """
    inputs = layers.Input(shape=input_shape, name="bilstm_input")
    
    # First Bi-LSTM layer
    x = layers.Bidirectional(
        layers.LSTM(
            BILSTM_UNITS_L1,
            return_sequences=True,
            dropout=BILSTM_DROPOUT,
            recurrent_dropout=BILSTM_RECURRENT_DROPOUT
        ),
        name="bilstm_l1"
    )(inputs)
    
    x = layers.BatchNormalization()(x)
    
    # Second Bi-LSTM layer (returns last step hidden state)
    x = layers.Bidirectional(
        layers.LSTM(
            BILSTM_UNITS_L2,
            return_sequences=False,
            dropout=BILSTM_DROPOUT,
            recurrent_dropout=BILSTM_RECURRENT_DROPOUT
        ),
        name="bilstm_l2"
    )(x)
    
    x = layers.BatchNormalization()(x)
    outputs = layers.Dense(64, activation="relu", name="bilstm_features")(x)
    
    model = Model(inputs=inputs, outputs=outputs, name="bilstm_branch")
    return model
