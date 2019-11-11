# default packages
import pathlib
import unittest
from typing import Tuple

# third party
import tensorflow as tf
from tqdm import tqdm

# my packages
from src.data import history
from src.data.checkpoint import Checkpoint
from src.models import dense_ae as network
from src.visualization import visualize


class TestNetwork(unittest.TestCase):
    """ネットワークの学習を簡易に実行する。
    """

    def test_train(self):
        # training parameters
        image_shape = (28, 28, 1)
        epochs = 5
        batch_size = 128
        dims = image_shape[0] * image_shape[1]
        (x_train, _), _ = tf.keras.datasets.mnist.load_data()
        train_ds = (
            tf.data.Dataset.from_tensor_slices(x_train)
            .map(lambda x: _convert_types(x, dims))
            .shuffle(10000)
            .batch(batch_size)
        )

        # training
        model = _train(train_ds, image_shape, epochs)

        # test
        reconstruct = model([data for data in train_ds.take(1)][0])
        input_dims = image_shape[0] * image_shape[1] * image_shape[2]
        self.assertEqual(reconstruct.shape, (batch_size, input_dims))


def _train(
    dataset: tf.data.Dataset, image_shape: Tuple[int, int, int], epochs: int
) -> tf.keras.Model:
    """学習処理を指定エポック数実行する

    Args:
        dataset (tf.data.Dataset): 学習データセット
        image_shape (Tuple[int, int, int]): 学習画像一枚当たりのサイズ
        epochs (int): 学習するエポック数

    Returns:
        tf.keras.Model: 学習したモデル
    """
    input_shape = image_shape[0] * image_shape[1] * image_shape[2]
    output_base = pathlib.Path("data/dense_ae")
    history_filepath = output_base.joinpath("history.pkl")
    history_imagepath = output_base.joinpath("history.png")
    reconstruct_filepath = output_base.joinpath("reconstruct.png")

    model = network.Autoencoder(input_shape)
    optimizer = tf.keras.optimizers.Adam(1e-4)
    loss = tf.keras.losses.mean_squared_error

    checkpoint = Checkpoint(
        save_dir=str(output_base.joinpath("ckpts")),
        max_to_keep=3,
        restore=True,
        model=model,
        optimizer=optimizer,
    )
    epoch_history = history.restore(history_filepath)
    input_example = [data for data in dataset.take(1)][-1]
    progress_bar = tqdm(range(checkpoint.save_counter(), epochs))
    for epoch in progress_bar:
        # learning
        batch_history = history.Batch()
        for batch in dataset:
            model.train_step(batch, loss, optimizer, batch_history)

        # save results
        checkpoint.save()
        batch_history.result()
        epoch_history.result(batch_history)
        history.save(epoch_history, history_filepath)

        # show results
        progress_bar.set_description(f"epoch: {epoch}, {epoch_history.get_latest()}")
        history.show_image(epoch_history, filepath=history_imagepath)
        visualize.show_images(
            input_example,
            network.reconstruct(model, input_example),
            image_shape,
            reconstruct_filepath,
        )

    return model


def _convert_types(image: tf.Tensor, dims: int) -> tf.Tensor:
    """入力データセットを成型する

    Args:
        image (tf.Tensor): 入力画像
        dims (int): 1次元配列とするときの次元数

    Returns:
        tf.Tensor: 変換した画像
    """
    image = tf.cast(image, tf.float32)
    image /= 255.0
    image = tf.reshape(image, [dims])
    return image
