"""
MesoNet: a small CNN for face-forgery (deepfake) detection.

Architecture from the original paper/repo:
"MesoNet: a Compact Facial Video Forgery Detection Network" (Afchar et al., 2018)
https://github.com/DariusAf/MesoNet

Rewritten here against modern tf.keras (the original repo uses an old
standalone-Keras API that will error on current TensorFlow versions).
"""

from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import (
    Input, Dense, Flatten, Conv2D, MaxPooling2D,
    BatchNormalization, Dropout, LeakyReLU
)

IMG_WIDTH = 256  # MesoNet expects 256x256 RGB face crops


class Meso4:
    """
    The 'Meso4' variant from the paper — 4 conv blocks + small dense head.
    Output: a single sigmoid value.
    Convention used by the original pretrained weights:
        close to 1.0  -> REAL
        close to 0.0  -> FAKE
    (We flip this into a human-readable label in detect.py.)
    """

    def __init__(self, learning_rate: float = 0.001):
        self.model = self._build()
        self.model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss="mean_squared_error",
            metrics=["accuracy"],
        )

    def _build(self) -> Model:
        x = Input(shape=(IMG_WIDTH, IMG_WIDTH, 3))

        x1 = Conv2D(8, (3, 3), padding="same", activation="relu")(x)
        x1 = BatchNormalization()(x1)
        x1 = MaxPooling2D(pool_size=(2, 2), padding="same")(x1)

        x2 = Conv2D(8, (5, 5), padding="same", activation="relu")(x1)
        x2 = BatchNormalization()(x2)
        x2 = MaxPooling2D(pool_size=(2, 2), padding="same")(x2)

        x3 = Conv2D(16, (5, 5), padding="same", activation="relu")(x2)
        x3 = BatchNormalization()(x3)
        x3 = MaxPooling2D(pool_size=(2, 2), padding="same")(x3)

        x4 = Conv2D(16, (5, 5), padding="same", activation="relu")(x3)
        x4 = BatchNormalization()(x4)
        x4 = MaxPooling2D(pool_size=(4, 4), padding="same")(x4)

        y = Flatten()(x4)
        y = Dropout(0.5)(y)
        y = Dense(16)(y)
        y = LeakyReLU(alpha=0.1)(y)
        y = Dropout(0.5)(y)
        y = Dense(1, activation="sigmoid")(y)

        return Model(inputs=x, outputs=y)

    def load_weights(self, weights_path: str):
        self.model.load_weights(weights_path)

    def predict(self, face_batch):
        """face_batch: numpy array of shape (N, 256, 256, 3), values in [0,1]."""
        return self.model.predict(face_batch, verbose=0)
