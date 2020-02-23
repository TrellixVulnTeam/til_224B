# Autoencoder using PyTorch

PyTorch を利用した Autoencoder 実装です。
対象データは、時系列データとしてます。

## 環境構築

Poetry で管理しているため、下記コマンドで環境構築できます。

```sh
poetry install
```

## Usage

学習は下記のように実行します。

```sh
python -m src.models.train SimpleAE
```
