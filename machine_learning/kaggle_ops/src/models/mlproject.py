"""MLProjectを利用した実行スクリプト."""
# default packages
import dataclasses
import logging
import os
import pathlib
import sys
import typing as t

# third party packages
import mlflow.projects as mlf_projects
import mlflow.tracking as mlf_tracking
import mlflow.exceptions as mlf_exceptions
import yaml

# logger
_logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Config:
    """スクリプト実行用設定値."""

    experiment_name: str = "default"

    uri: t.Optional[str] = None
    git_version: t.Optional[str] = None


def main(config: Config) -> None:
    MLFLOW_ARTIFACT_LOCATION = os.environ.get(
        "MLFLOW_ARTIFACT_LOCATION", "./data/processed/mlruns/artifacts"
    )

    client = mlf_tracking.MlflowClient()
    try:
        _ = client.create_experiment(
            config.experiment_name,
            artifact_location=MLFLOW_ARTIFACT_LOCATION,
        )
    except mlf_exceptions.MlflowException:
        pass

    params = {}
    if config.git_version is not None:
        params["version"] = config.git_version

    mlf_projects.run(
        config.uri,
        entry_point="main",
        experiment_name=config.experiment_name,
        use_conda=False,
        **params,
    )


def _load_config(filepath: pathlib.Path) -> Config:
    """設定ファイルを読み込む."""
    with open(str(filepath), "r") as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
    config = Config(**data)

    return config


if __name__ == "__main__":
    try:
        debug_mode = True if os.environ.get("MODE_DEBUG", "") == "True" else False
        logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)

        if len(sys.argv) == 2:
            _config = _load_config(pathlib.Path(sys.argv[1]))
        else:
            _config = Config()

        main(_config)
    except Exception as e:
        _logger.exception(e)
        sys.exit("Fail")
