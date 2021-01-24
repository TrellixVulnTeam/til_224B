#!/bin/bash
#
# Run MLflow traking server.
# Usage: bash run_mlflow_tracking_server.sh

set -eu

readonly SCRIPT_DIR=$(cd $(dirname $0); pwd)
readonly PROJECT_DIR=$SCRIPT_DIR
readonly HOST=${SERVER_HOST:-"127.0.0.1"}
readonly PORT=${SERVER_PORT:-"5000"}
readonly BACKEND_STORE_URI=${BACKEND_STORE_URI:-"sqlite:///mlruns/tracking.db"}
readonly ARTIFACT_STORE=${ARTIFACT_STORE:-"$PROJECT_DIR/mlruns"}

mlflow server \
  --backend-store-uri=$BACKEND_STORE_URI \
  --default-artifact-root=$ARTIFACT_STORE \
  --host=$HOST