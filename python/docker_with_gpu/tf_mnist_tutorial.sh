#!/bin/bash

docker run \
  --rm \
  -t \
  --gpus all \
  -u $(id -u):$(id -g) \
  --mount type=bind,source="$(pwd)",target=/workspace,readonly \
  -w /workspace \
  tensorflow/tensorflow:2.1.0-gpu-py3 \
  python tf_mnist_tutorial.py
