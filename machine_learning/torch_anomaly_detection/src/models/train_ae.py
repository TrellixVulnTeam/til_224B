"""Autoencoder 系の学習用スクリプト."""
# default
import argparse
import dataclasses as dc
import enum
import logging
import pprint
import random
import shutil
import sys
import typing as t

# third party
import matplotlib.pyplot as plt
import numpy as np
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks
import pytorch_lightning.logging as pl_logging
import torch
import torch.nn as nn
import torch.cuda as tc
import torch.optim as optim
import torch.optim.lr_scheduler as lr_scheduler
import torch.utils.data as td
import torchvision.transforms as tv_transforms

# my packages
import src.data.mvtecad as mvtecad
import src.data.mvtecad_torch as mvtecad_torch
import src.data.celeba_torch as celeba
import src.data.dataset_torch as ds
import src.data.directories as directories
import src.data.utils as ut
import src.models.cnn_ae as cnn_ae

# logger
_logger = logging.getLogger(__name__)


class AETrainer(pl.LightningModule):
    """Autoencoder 用の学習クラス."""

    def __init__(self, network: nn.Module, record_params: t.Dict = dict()) -> None:
        super(AETrainer, self).__init__()

        self.network = network
        self.hparams = argparse.Namespace(**record_params)
        self.criterion = nn.BCEWithLogitsLoss()
        self.learning_rate = 1e-2
        self.sgd_momentum = 0.9

    def forward(self, x):
        return self.network(x)

    def training_step(self, batch, batch_nb):
        decode = self.forward(batch)
        loss = self.criterion(decode, batch)

        if batch_nb % 100 == 0:
            num_display = 4
            fig = _create_graph(
                batch[:num_display].detach().cpu().numpy(),
                decode[:num_display].detach().cpu().numpy(),
            )
            self.logger.experiment.add_figure(
                tag="train/reconstruct", figure=fig, global_step=self.global_step,
            )
            fig.clf()
            plt.close()

        tensorboard_logs = {"train/loss": loss}

        return {"loss": loss, "log": tensorboard_logs}

    def training_epoch_end(self, outputs):
        avg_loss = torch.stack([x["loss"] for x in outputs]).mean()

        tensorboard_logs = {"train/epoch_loss": avg_loss}
        return {"train_loss": avg_loss, "log": tensorboard_logs}

    def validation_step(self, batch, batch_nb):
        decode = self.forward(batch)
        loss = self.criterion(decode, batch)

        if batch_nb % 100 == 0:
            num_display = 4
            fig = _create_graph(
                batch[:num_display].detach().cpu().numpy(),
                decode[:num_display].detach().cpu().numpy(),
            )
            self.logger.experiment.add_figure(
                tag="valid/reconstruct", figure=fig, global_step=self.global_step,
            )
            fig.clf()
            plt.close()

        tensorboard_logs = {"valid/loss": loss}

        return {"val_loss": loss, "log": tensorboard_logs}

    def validation_epoch_end(self, outputs):
        avg_loss = torch.stack([x["val_loss"] for x in outputs]).mean()

        tensorboard_logs = {"valid/epoch_loss": avg_loss}
        return {"val_loss": avg_loss, "log": tensorboard_logs}

    def configure_optimizers(self):
        optimizer = optim.SGD(
            self.parameters(), lr=self.learning_rate, momentum=self.sgd_momentum
        )
        scheduler = lr_scheduler.ReduceLROnPlateau(optimizer)

        return [optimizer], [scheduler]

    @pl.data_loader
    def train_dataloader(self):
        return self.dataloader_train

    @pl.data_loader
    def val_dataloader(self):
        return self.dataloader_valid

    def set_dataloader(self, train: td.DataLoader, valid: td.DataLoader) -> None:
        self.dataloader_train = train
        self.dataloader_valid = valid


@dc.dataclass
class Config:
    dataset_name: str = "MVTecAD_Hazelnut"
    network_name: str = "SimpleCBR"
    in_channels: int = 3
    out_channels: int = 3
    resize_image: t.Tuple[int, int] = (64, 64)

    batch_size: int = 144
    num_workers: int = 4

    random_seed: int = 42

    cache_dir: str = "simple_cbr_mvtecad_hazelnut"
    save_top_k: int = 2
    save_weights_only: bool = False

    experiment_version: int = 0
    resume: bool = False

    early_stop: bool = True
    min_epochs: int = 2
    max_epochs: int = 2

    log_dir: str = "train_ae"
    use_gpu: bool = True
    progress_bar_refresh_rate: int = 1
    profiler: bool = True


class DatasetName(enum.Enum):
    """データセットを指定するための設定値."""

    CELEBA = "CelebA"
    MVTECAD_HAZELNUT = "MVTecAD_Hazelnut"

    @classmethod
    def value_of(cls, name: str) -> "DatasetName":
        """設定値の文字列から Enum 値を返す.

        Raises:
            ValueError: 指定した文字列が設定値にない場合

        Returns:
            [type]: Enum の値
        """
        for e in DatasetName:
            if e.value == name:
                return e

        raise ValueError(f"invalid value: {name}")


class NetworkName(enum.Enum):
    """ネットワークを指定するための設定値."""

    SIMPLE_CBR = "SimpleCBR"
    SIMPLE_CR = "SimpleCR"

    @classmethod
    def value_of(cls, name: str) -> "NetworkName":
        """設定値の文字列から Enum 値を返す.

        Raises:
            ValueError: 指定した文字列が設定値にない場合

        Returns:
            [type]: Enum の値
        """
        for e in NetworkName:
            if e.value == name:
                return e

        raise ValueError(f"invalid value: {name}")


def get_dataset(
    name: DatasetName, transforms: tv_transforms.Compose, **kwargs
) -> t.Tuple[td.Dataset, td.Dataset]:
    if name == DatasetName.CELEBA:
        dataset_train = celeba.DatasetAE(transforms=transforms, mode=ds.Mode.TRAIN)
        dataset_valid = celeba.DatasetAE(transforms=transforms, mode=ds.Mode.VALID)
        return dataset_train, dataset_valid

    if name == DatasetName.MVTECAD_HAZELNUT:
        dataset_train = mvtecad_torch.DatasetAE(
            kind=mvtecad.Kind.HAZELNUT, transforms=transforms, mode=ds.Mode.TRAIN
        )
        dataset_valid = mvtecad_torch.DatasetAE(
            kind=mvtecad.Kind.HAZELNUT, transforms=transforms, mode=ds.Mode.VALID
        )
        return dataset_train, dataset_valid

    raise Exception(f"not implemented dataset: {name}")


def get_network(name: NetworkName, **kwargs) -> nn.Module:
    if name == NetworkName.SIMPLE_CBR:
        return cnn_ae.SimpleCBR(**kwargs)

    if name == NetworkName.SIMPLE_CR:
        return cnn_ae.SimpleCR(**kwargs)

    raise Exception(f"not implemented network: {name}")


def get_transforms(image_size: t.Tuple[int, int]) -> tv_transforms.Compose:
    """データ変換コンポーネントの取得.

    Args:
        image_size (Tuple[int, int]): 最終的に取得する画像サイズ.

    Returns:
        torchvision.transforms.Compose: データ変換コンポーネント
    """
    transforms = tv_transforms.Compose(
        [
            tv_transforms.RandomHorizontalFlip(),
            # tv_transforms.CenterCrop(148),
            tv_transforms.Resize(image_size),
            tv_transforms.ToTensor(),
        ]
    )

    return transforms


def train(config: Config):
    """学習処理の実行スクリプト."""
    transforms = get_transforms(config.resize_image)
    dataset_type = DatasetName.value_of(config.dataset_name)
    dataset_train, dataset_valid = get_dataset(dataset_type, transforms)

    dataloader_train = td.DataLoader(
        dataset_train,
        config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
        pin_memory=True,
        worker_init_fn=_worker_init_random,
    )
    dataloader_valid = td.DataLoader(
        dataset_valid,
        config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=True,
        worker_init_fn=_worker_init_random,
    )

    params = dc.asdict(config)
    pl.seed_everything(config.random_seed)

    network = get_network(
        NetworkName.value_of(config.network_name),
        in_channels=config.in_channels,
        out_channels=config.out_channels,
    )
    model = AETrainer(network, params)
    model.set_dataloader(dataloader_train, dataloader_valid)

    cache_dir = directories.get_processed().joinpath(config.cache_dir)
    cache_dir.mkdir(exist_ok=True)
    model_checkpoint = pl_callbacks.ModelCheckpoint(
        filepath=str(cache_dir),
        monitor="val_loss",
        save_last=True,
        save_top_k=config.save_top_k,
        save_weights_only=config.save_weights_only,
        mode="min",
        period=1,
    )

    experiment_dir = cache_dir.joinpath(
        "default", f"version_{config.experiment_version}"
    )
    pl_logger = pl_logging.TensorBoardLogger(
        save_dir=str(experiment_dir), version=config.experiment_version
    )
    trainer_params = dict()
    if config.resume:
        trainer_params["resume_from_checkpoint"] = str(cache_dir.joinpath("last.ckpt"))
    elif experiment_dir.exists():
        shutil.rmtree(experiment_dir)
        for filepath in cache_dir.glob("epoch=*.ckpt"):
            filepath.unlink()

    pl_trainer = pl.Trainer(
        early_stop_callback=config.early_stop,
        default_root_dir=str(cache_dir),
        fast_dev_run=False,
        min_epochs=config.min_epochs,
        max_epochs=config.max_epochs,
        gpus=[0] if config.use_gpu and tc.is_available() else None,
        progress_bar_refresh_rate=config.progress_bar_refresh_rate,
        profiler=config.profiler,
        checkpoint_callback=model_checkpoint,
        logger=pl_logger,
        **trainer_params,
    )
    pl_trainer.fit(model)

    ckptfile = sorted(cache_dir.glob("epoch*.ckpt"))[-1]
    model = model.load_from_checkpoint(str(ckptfile), network, params)
    torch.save(model.network.state_dict(), cache_dir.joinpath(ckptfile.stem))


def _create_graph(batch: np.ndarray, decode: np.ndarray) -> None:
    batch = batch.transpose(0, 2, 3, 1)
    decode = decode.transpose(0, 2, 3, 1)

    params_imshow = dict()
    if batch.shape[3] == 1:
        batch = batch.reshape(batch.shape[:3])
        decode = decode.reshape(decode.shape[:3])
        params_imshow["cmap"] = "gray"

    rows, cols = 2, batch.shape[0]
    figsize = (4 * cols, 4 * rows)
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    for idx in range(cols):
        ax = axes[0, idx]
        ax.imshow(batch[idx], **params_imshow)

        ax = axes[1, idx]
        ax.imshow(decode[idx], **params_imshow)

    return fig


def _worker_init_random(worker_id: int) -> None:
    random.seed(worker_id)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)

        if len(sys.argv) == 1:
            _config = Config()
        elif len(sys.argv) == 2:
            _config = ut.load_yaml(sys.argv[1], lambda d: Config(**d))
        else:
            raise Exception(
                "input arguments error."
                " usage: python path/to/script.py"
                " or python path/to/script.py path/to/config.yml"
            )
        _logger.info(f"config: {pprint.pformat(dc.asdict(_config))}")

        train(_config)
    except Exception as e:
        _logger.exception(e)
