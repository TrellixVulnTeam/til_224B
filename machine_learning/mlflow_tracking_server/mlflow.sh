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

# sync settings.
readonly LOCAL_MLRUNS=${LOCAL_MLRUNS:-"$PROJECT_DIR/mlruns"}
readonly LOCAL_ARTIFACTS=${LOCAL_ARTIFACTS:-"$PROJECT_DIR/artifacts"}
readonly REMOTE_MLRUNS=${REMOTE_MLRUNS:-"$PROJECT_DIR/mlruns"}
readonly REMOTE_ARTIFACTS=${REMOTE_ARTIFACTS:-"$PROJECT_DIR/artifacts"}

# glcoud settings.
readonly GCLOUD_CONFIG=${GCLOUD_CONFIG:-"$HOME/.config/gcloud"}
readonly GCS_BUCKET_NAME=${GCS_BUCKET_NAME:-""}

# HELP.
function _usage() {
  cat <<EOF
$SCRIPT_NAME is a tool for mlflow.

Usage:
$SCRIPT_NAME [command] [options]

Commands:
docker:      use docker.
  build:     build docker image.
  command:   run $SCRIPT_NAME in docker container.
  daemon:    run command in docker daemon.
  exec:      execute command.
  help:      print this.
  logs:      show logs.
  rm:        remove container.
  rmi:       remove iamge.
  run:       run command in docker container.
  start:     start container.
  stop:      stop container.
experiments: run mlflow experiments command.
gc:          garbage collection.
gcs:         google cloud storage.
  clone:     clone mlruns from gcs.
  delete:    delete files in gcs.
  mirror:    delete files in local.
  upload:    upload mlruns to gcs.
help:        print this.
server:      run mlflow tracking server.
sync:        sync local and remote files.
  delete:    delete files from local.
  help:      print this.
  meta:      sync local and remote meta.yml.
  upload:    upload all files.
ui:          run mlflow tracking ui.
EOF
}

# Command using docker.
function _docker() {
  local readonly SUB_COMMAND=$1
  shift
  local readonly SUB_OPTIONS="$@"


  case "$SUB_COMMAND" in
    "build" ) _docker_build;;
    "command" ) _docker_command $SUB_OPTIONS;;
    "daemon" ) _docker_run -d $IMAGE_NAME bash $SCRIPT_NAME $SUB_OPTIONS;;
    "exec" ) docker exec -it $CONTAINER_NAME $SUB_OPTIONS;;
    "help") _usage;;
    "logs" ) docker logs $SUB_OPTIONS $CONTAINER_NAME;;
    "rm" ) docker rm $CONTAINER_NAME;;
    "rmi" ) docker rmi $IMAGE_NAME;;
    "run" ) _docker_run -it $IMAGE_NAME $SUB_OPTIONS;;
    "start") docker start $CONTAINER_NAME;;
    "stop") docker stop $CONTAINER_NAME;;
  esac
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

function _docker_command() {
  local readonly SUB_OPTIONS="$@"

  if [ "$(docker container ls -q -f name=${CONTAINER_NAME})" ]; then
    docker exec -it $CONTAINER_NAME bash $SCRIPT_NAME $SUB_OPTIONS
    return
  fi

  _docker_run -it $IMAGE_NAME bash $SCRIPT_NAME $SUB_OPTIONS
}

# Run docker container.
function _docker_run() {
  local gcloud_mount=""
  if [ -d $GCLOUD_CONFIG ]; then
    gcloud_mount="--mount=source=$GCLOUD_CONFIG,target=/opt/.config/gcloud,type=bind,consistency=cached"
  fi

  local mlruns_mount=""
  if [ -d $LOCAL_MLRUNS ]; then
    mlruns_mount="--mount=source=$LOCAL_MLRUNS,target=/mlflow/mlruns,type=bind,consistency=cached"
  fi
  local artifacts_mount=""
  if [ -d $LOCAL_ARTIFACTS ]; then
    artifacts_mount="--mount=source=$LOCAL_ARTIFACTS,target=/mlflow/artifacts,type=bind,consistency=cached"
  fi

  docker run \
    --rm \
    --name $CONTAINER_NAME \
    --env-file=$PROJECT_DIR/.env \
    -e=TZ="Asia/Tokyo" \
    --mount=source=$PROJECT_DIR,target=$PROJECT_DIR,type=bind,consistency=cached \
    $gcloud_mount \
    $mlruns_mount \
    $artifacts_mount \
    -p=127.0.0.1:$PORT:$PORT \
    -w=$PROJECT_DIR \
    --user ${CONTAINER_UID}:${CONTAINER_GID} \
    $@
}

function _experiments() {
  local readonly SUB_OPTIONS="$@"

  pushd $PROJECT_DIR
  mlflow experiments $SUB_OPTIONS
  popd
}

# Garbage collection.
function _gc() {
  local readonly SUB_OPTIONS="$@"

  pushd $PROJECT_DIR
  mlflow gc --backend-store-uri=$BACKEND_STORE_URI $SUB_OPTIONS
  popd
}

# Google Cloud Storage.
function _gcs() {
  local readonly SUB_COMMAND=$1
  shift
  local readonly SUB_OPTIONS="$@"


  case "$SUB_COMMAND" in
    "clone" ) _gcs_clone $SUB_OPTIONS;;
    "delete" ) _gcs_delete;;
    "mirror" ) _gcs_mirror;;
    "upload" ) _gcs_upload;;
  esac
}

# clone mlruns from gcs.
function _gcs_clone() {
  local readonly GCS_MLRUNS=gs://$GCS_BUCKET_NAME/$BACKEND_STORE_URI
  gsutil -m rsync -Jr $@ $GCS_MLRUNS $LOCAL_MLRUNS
}

# delete files in gcs.
function _gcs_delete() {
  local readonly GCS_MLRUNS=gs://$GCS_BUCKET_NAME/$BACKEND_STORE_URI
  gsutil -m rsync -dJr $@ $LOCAL_MLRUNS $GCS_MLRUNS
}

# delete files in local.
function _gcs_mirror() {
  local readonly GCS_MLRUNS=gs://$GCS_BUCKET_NAME/$BACKEND_STORE_URI
  gsutil -m rsync -dJr $@ $GCS_MLRUNS $LOCAL_MLRUNS
}

# upload files to gcs.
function _gcs_upload() {
  local readonly GCS_MLRUNS=gs://$GCS_BUCKET_NAME/$BACKEND_STORE_URI
  gsutil -m rsync -Jr $@ $LOCAL_MLRUNS $GCS_MLRUNS
}

# Run mlflow tracking server.
function _server() {
  local readonly SUB_OPTIONS="$@"

  pushd $PROJECT_DIR
  mlflow server \
    --backend-store-uri=$BACKEND_STORE_URI \
    --default-artifact-root=$ARTIFACT_STORE \
    --host=$HOST \
    --port=$PORT \
    $SUB_OPTIONS
  popd
}

function _sync() {
  local readonly SUB_COMMAND=$1
  shift
  local readonly SUB_OPTIONS="$@"

  case "$SUB_COMMAND" in
    "delete" ) _sync_delete $SUB_OPTIONS;;
    "download" ) _sync_download $SUB_OPTIONS;;
    "help" ) _usage;;
    "meta" ) _sync_meta $SUB_OPTIONS;;
    "upload") _sync_upload $SUB_OPTIONS;;
  esac
}

function _sync_delete() {
  local readonly SYNC_OPTIONS="$@"
  rsync -ahvz --delete $SYNC_OPTIONS $REMOTE_MLRUNS/ $LOCAL_MLRUNS/
  rsync -ahvz --delete $SYNC_OPTIONS $REMOTE_ARTIFACTS/ $LOCAL_ARTIFACTS/
}

function _sync_download() {
  local readonly SYNC_OPTIONS="$@"
  rsync -ahuvz $SYNC_OPTIONS $REMOTE_MLRUNS/ $LOCAL_MLRUNS/
  rsync -ahuvz $SYNC_OPTIONS $REMOTE_ARTIFACTS/ $LOCAL_ARTIFACTS/
}

# sync meta file.
function _sync_meta() {
  local readonly SYNC_OPTIONS="$@"
  rsync -ahuvz $SYNC_OPTIONS --include='*/' --include='meta.yaml' --exclude='*' $REMOTE_MLRUNS/ $LOCAL_MLRUNS/
}

function _sync_upload() {
  local readonly SYNC_OPTIONS="$@"
  rsync -ahuvz $SYNC_OPTIONS $LOCAL_MLRUNS/ $REMOTE_MLRUNS/
  rsync -ahuvz $SYNC_OPTIONS $LOCAL_ARTIFACTS/ $REMOTE_ARTIFACTS/
}

# Run mlflow tracking ui
function _ui() {
  local readonly SUB_OPTIONS="$@"

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
  "gcs" ) _gcs $OPTIONS;;
  "server") _server $OPTIONS;;
  "sync") _sync $OPTIONS;;
  "ui") _ui $OPTIONS;;
  "experiments") _experiments $OPTIONS;;
esac
