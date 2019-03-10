import pathlib
import pickle
from typing import Dict, List

import torch
from discriminator import Discriminator
from generator import Generator
from torch import nn, optim
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.utils import save_image


def format_history(d_loss: float, g_loss: float):
    """ 1 回分のデータを整形して返す
    """
    return {"d_loss": d_loss, "g_loss": g_loss}


def generate(generator: torch.nn, z_dim: int, image_num: int, is_cuda: bool):
    """ generator から画像を生成する
    """
    z = set_device(torch.rand((image_num, z_dim)), is_cuda)
    with torch.no_grad():
        z = Variable(z, volatile=True)
        samples = generator(z).data.cpu()
    return samples


def get_data_loader(batch_size: int):
    """ Get dataloader.

    Parameters
    ---
    batch_size : int
        バッチサイズ
    """
    transform = transforms.Compose([transforms.ToTensor()])
    dataset = datasets.MNIST(
        "data/mnist", train=True, download=True, transform=transform
    )
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    return data_loader


def run():
    """ Run training.
    """
    # hyper parameters
    batch_size = 128
    learning_rate = 2e-4
    z_dim = 62
    num_epochs = 2
    checkpoint_save_image_num = 64
    log_dir = pathlib.Path("./logs")
    log_dir.mkdir(exist_ok=True)

    # check cuda
    is_cuda = torch.cuda.is_available()
    print(f"cuda state: {is_cuda}")

    # initialize network
    generator = set_device(Generator(), is_cuda)
    discriminator = set_device(Discriminator(), is_cuda)

    # optimizer
    g_optimizer = optim.Adam(
        generator.parameters(), lr=learning_rate, betas=(0.5, 0.999)
    )
    d_optimizer = optim.Adam(
        discriminator.parameters(), lr=learning_rate, betas=(0.5, 0.999)
    )

    # loss
    criterion = nn.BCELoss()

    # datasets
    data_loader = get_data_loader(batch_size)

    # training
    history = []
    for epoch in range(num_epochs):
        d_loss, g_loss = train_one_epoch(
            discriminator,
            generator,
            criterion,
            d_optimizer,
            g_optimizer,
            data_loader,
            batch_size,
            z_dim,
            is_cuda,
        )
        save_checkpoint(discriminator, generator, epoch, log_dir)
        save_image(
            generate(generator, z_dim, checkpoint_save_image_num, is_cuda),
            log_dir.joinpath(f"epoch_{epoch:03}.png"),
        )
        history.append(format_history(d_loss, g_loss))
        print(f"epoch {epoch}, d_loss: {d_loss:.4}, g_loss: {g_loss:.4}")

    save_history(history, log_dir)


def save_checkpoint(
    discriminator: nn.Module, generator: nn.Module, epoch: int, log_dir: pathlib.Path
) -> None:
    """ save checkpoint.
    """
    torch.save(
        generator.state_dict(), str(log_dir.joinpath(f"generator_{epoch:03}.pth"))
    )
    torch.save(
        discriminator.state_dict(),
        str(log_dir.joinpath(f"discriminator_{epoch:03}.pth")),
    )


def save_history(history: List[Dict[str, str]], log_dir: pathlib.Path) -> None:
    """ save history.
    """
    with open(log_dir.joinpath("history.pkl", "wb")) as f:
        pickle.dump(history, f)


def train_one_epoch(
    discriminator: nn.Module,
    generator: nn.Module,
    criterion,
    d_optimizer,
    g_optimizer,
    data_loader: DataLoader,
    batch_size: int,
    z_dim: int,
    is_cuda: bool,
):
    """ Learn 1 epoch.

    Parameters
    ---

    discriminator : nn.Module
    generator : nn.Module
    criterion
    d_optimizer
    g_optimizer
    data_loader
    batch_size : int
        バッチサイズ
    z_dim : int
        入力ランダムベクトルの次元数
    is_cuda : bool
        True の場合に、 cuda を利用する
    """
    # 訓練モード
    discriminator.train()
    generator.train()

    # ラベル設定
    label_real = set_device(Variable(torch.ones(batch_size, 1)), is_cuda)
    label_fake = set_device(Variable(torch.zeros(batch_size, 1)), is_cuda)

    data_size = 0
    d_running_loss = 0
    g_running_loss = 0
    for batch_idx, (real_images, _) in enumerate(data_loader):
        # 最後のバッチでバッチ数が足りない場合は無視する
        if real_images.size()[0] != batch_size:
            break
        data_size += batch_size

        # Discriminator が real 画像を real と判定できるか
        d_optimizer.zero_grad()
        d_real = discriminator(Variable(set_device(real_images, is_cuda)))
        d_real_loss = criterion(d_real, label_real)

        # Discriminator 用に fake 画像を生成し、
        # Discriminator が fake と判定できるか
        z = Variable(set_device(torch.rand((batch_size, z_dim)), is_cuda))
        fake_images = generator(z)
        d_fake = discriminator(fake_images.detach())
        d_fake_loss = criterion(d_fake, label_fake)

        # 2 つの loss の最小化
        d_loss = d_real_loss + d_fake_loss
        d_loss.backward()
        d_optimizer.step()
        d_running_loss += d_loss.data

        # Generator が生成した画像を Discriminator に real と判定させられるか
        g_optimizer.zero_grad()
        z = Variable(set_device(torch.rand((batch_size, z_dim)), is_cuda))
        fake_images = generator(z)
        d_fake = discriminator(fake_images)
        g_loss = criterion(d_fake, label_real)
        g_loss.backward()
        g_optimizer.step()
        g_running_loss += g_loss.data

    d_running_loss /= data_size
    g_running_loss /= data_size

    return d_running_loss, g_running_loss


def set_device(src, is_cuda):
    """ CUDA デバイス対応に変換する
    """
    if is_cuda:
        return src.cuda()
    return src


if __name__ == "__main__":
    run()
