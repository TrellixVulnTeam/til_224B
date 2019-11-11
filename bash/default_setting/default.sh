#!/bin/bash

# シェルスクリプトの実行においてセーフティネットを有効化しておく
# e: 失敗コマンドを実行時にスクリプトを停止する
# u: 未定義変数を利用した時点でスクリプトを停止する
set -eu

# 失敗するコマンドなので下記部分で停止する
rm temp

# 一時的に失敗処理をしても停止しないようにする。
set +e
rm temp
set -e

# 下記部分は未定義変数を利用するため停止する
rm $TEMP_DIR