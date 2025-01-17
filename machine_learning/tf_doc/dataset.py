import numpy as np

from logging import getLogger
from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.utils import to_categorical
from typing import Tuple

logger = getLogger(__name__)


def get_fasion_mnist() -> (
    Tuple[np.ndarray, np.ndarray, np.ndarray],
    Tuple[np.ndarray, np.ndarray],
):
    width, height, channels = 28, 28, 1

    (x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
    x_train = x_train.reshape(x_train.shape[0], width, height, channels)
    x_test = x_test.reshape(x_test.shape[0], width, height, channels)
    x_train = x_train.astype("float32") / 255
    x_test = x_test.astype("float32") / 255

    x_train_s, x_test_s, x_test_b = [], [], []
    x_ref, y_ref = [], []
    x_train_shape = x_train.shape

    for i in range(len(x_train)):
        if y_train[i] == 7:  # スニーカーの ID
            temp = x_train[i]
            x_train_s.append(temp.reshape((x_train_shape[1:])))
        else:
            temp = x_train[i]
            x_ref.append(temp.reshape((x_train_shape[1:])))
            y_ref.append(y_train[i])
    logger.info(f"x_train_s: length = {len(x_train_s)}, shape = {x_train_s[0].shape}")
    logger.info(f"x_ref: length = {len(x_ref)}, shape = {x_ref[0].shape}")
    logger.info(f"y_ref: length = {len(y_ref)}, shape = {y_ref[0].shape}")

    np.random.seed(0)
    x_ref = np.array(x_ref)
    number = np.random.choice(np.arange(0, x_ref.shape[0]), 6000, replace=False)
    x, y = [], []
    x_ref_shape = x_ref.shape
    for i in number:
        temp = x_ref[i]
        x.append(temp.reshape((x_ref_shape[1:])))
        y.append(y_ref[i])
    logger.info(f"x: length = {len(x)}, shape = {x[0].shape}")
    logger.info(f"y: length = {len(y)}, shape = {y[0].shape}")

    x_train_s = np.array(x_train_s)
    x_ref = np.array(x)
    y_ref = to_categorical(y)

    for i in range(len(x_test)):
        if y_test[i] == 7:  # スニーカーのID
            temp = x_test[i, :, :, :]
            x_test_s.append(temp.reshape((x_train_shape[1:])))
        if y_test[i] == 9:
            temp = x_test[i, :, :, :]
            x_test_b.append(temp.reshape((x_train_shape[1:])))
    x_test_s = np.array(x_test_s)
    x_test_b = np.array(x_test_b)

    return (x_train_s, x_ref, y_ref), (x_test_s, x_test_b)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)

    get_fasion_mnist()
