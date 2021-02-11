#!/bin/bash
#
# MLFlowで良く利用するコマンド群の定義。

set -eu

readonly SCRIPT_PATH=${0}
readonly SCRIPT_DIR=$(cd $(dirname $SCRIPT_PATH); pwd)
readonly SCRIPT_NAME=$(basename $SCRIPT_PATH)
readonly PROJECT_DIR=$SCRIPT_DIR

# MLFlow settings.
readonly BACKEND_STORE_URI=${BACKEND_STORE_URI:-"sqlite:///mlruns/tracking.db"}
readonly ARTIFACT_STORE=${ARTIFACT_STORE:-"$PROJECT_DIR/mlruns"}
readonly HOST=${SERVER_HOST:-"127.0.0.1"}
readonly PORT=${SERVER_PORT:-"5000"}

# container settings.
readonly USER=${USER:-"dev"}
readonly IMAGE_NAME=${IMAGE_NAME:-"${USER}/mlflow:latest"}
readonly CONTAINER_NAME=${CONTAINER_NAME:-"${USER}_mlflow"}
readonly CONTAINER_UID=${CONTAINER_UID:-$(id -u)}
readonly CONTAINER_GID=${CONTAINER_GID:-$(id -g)}
readonly CONTAINER_USER=${CONTAINER_USER:-"$USER"}

# HELP.
function _usage() {
  cat <<EOF
$SCRIPT_NAME is a tool for mlflow.

Usage:
$SCRIPT_NAME [command] [options]

Commands:
docker:  use docker.
gc:      garbage collection.
help:    print this.
server:  run mlflow tracking server.
ui:      run mlflow tracking ui.
EOF
}

# Command using docker.
function _docker() {
  readonly SUB_COMMAND=$1
  shift
  readonly SUB_OPTIONS="$@"

  case "$SUB_COMMAND" in
    "build" ) _docker_build;;
    "command" ) docker exec -it $CONTAINER_NAME bash $SCRIPT_NAME $SUB_OPTIONS;;
    "daemon" ) _docker_run -d $IMAGE_NAME bash $SCRIPT_NAME $SUB_OPTIONS;;
    "exec" ) docker exec -it $CONTAINER_NAME $SUB_OPTIONS;;
    "logs" ) docker logs $SUB_OPTIONS $CONTAINER_NAME;;
    "rm" ) docker rm $CONTAINER_NAME;;
    "rmi" ) docker rmi $IMAGE_NAME;;
    "run" ) _docker_run -it $IMAGE_NAME bash $SCRIPT_NAME $SUB_OPTIONS;;
    "start") docker start $CONTAINER_NAME;;
    "stop") docker stop $CONTAINER_NAME;;
  esac
}

# HELP for command using docker.
function _docker_usage() {
  cat <<EOF
$SCRIPT_NAME is a tool for mlflow using docker.

Usage:
$SCRIPT_NAME docker [command] [options]

Commands:
build:   build docker image.
command: run $SCRIPT_NAME in docker container.
daemon:  run command in docker daemon.
exec:    execute command.
logs:    show logs.
rm:      remove container.
rmi:     remove iamge.
run:     run command in docker container.
start:   start container.
stop:    stop container.
EOF
}

# Build docker image.
function _docker_build() {
  pushd $PROJECT_DIR
  docker build \
    --force-rm \
    -f Dockerfile \
    -t $IMAGE_NAME \
    .
  popd
}

# Run docker container.
function _docker_run() {
  readonly WORKSPACE="/workspace"

  docker run \
    --rm \
    --name $CONTAINER_NAME \
    --env-file=$PROJECT_DIR/.env \
    -e=TZ="Asia/Tokyo" \
    --mount=source=$PROJECT_DIR,target=$PROJECT_DIR,type=bind,consistency=cached \
    -p=127.0.0.1:$PORT:$PORT \
    -w=$PROJECT_DIR \
    --user ${CONTAINER_UID}:${CONTAINER_GID} \
    $@
}

# Garbage collection.
function _gc() {
  readonly SUB_OPTIONS="$@"

  pushd $PROJECT_DIR
  mlflow gc --backend-store-uri=$BACKEND_STORE_URI $SUB_OPTIONS
  popd
}

# Run mlflow tracking server.
function _server() {
  readonly SUB_OPTIONS="$@"

  pushd $PROJECT_DIR
  mlflow server \
    --backend-store-uri=$BACKEND_STORE_URI \
    --default-artifact-root=$ARTIFACT_STORE \
    --host=$HOST \
    --port=$PORT \
    $SUB_OPTIONS
  popd
}

# Run mlflow tracking ui
function _ui() {
  readonly SUB_OPTIONS="$@"

  pushd $PROJECT_DIR
  mlflow ui \
    --backend-store-uri=$BACKEND_STORE_URI \
    --default-artifact-root=$ARTIFACT_STORE \
    --host=$HOST \
    --port=$PORT \
    $SUB_OPTIONS
  popd
}

# Run script
readonly COMMAND=$1
shift
readonly OPTIONS="$@"

case "$COMMAND" in
  "help" ) _usage;;
  "docker") _docker $OPTIONS;;
  "gc" ) _gc $OPTIONS;;
  "server") _server $OPTIONS;;
  "ui") _ui $OPTIONS;;
esac

