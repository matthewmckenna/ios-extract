import json
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import pathify


@dataclass
class Config:
    uuid: str
    output_directory: Path

    def __post_init__(self):
        self.output_directory = pathify(self.output_directory)


def get_project_directory() -> Path:
    """Return the project directory path.

    The project directory is used to find the `config.toml`
    file, and to create the `logs` directory.

    The directory tree for this file is as follows:

    iostoolbox_project  # project directory / repository
    └── iostoolbox
        └── config.py

    Path(__file__) == Path("config.py")
    Path(__file__).parent == Path("iostoolbox")
    Path(__file__).parent.parent == Path("iostoolbox_project")
    """
    return Path(__file__).parent.parent


def get_default_config_filepath() -> Path:
    """Return the default config filepath"""
    project_directory = get_project_directory()
    return project_directory / "config.toml"


def load_config(filepath: Path | str) -> Config:
    """Load a config file and return as a Config object"""
    config_dict = load_config_dict(filepath)
    return Config(**config_dict["iostoolbox"])


def load_config_dict(filepath: Path | str) -> dict[str, Any]:
    """Load a config file and return as a dict.

    Supported file formats:
      - TOML
      - JSON
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)
    with open(filepath, "rb") as f:
        if filepath.suffix == ".toml":
            config_dict = tomllib.load(f)
        elif filepath.suffix == ".json":
            config_dict = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
    return config_dict


def load_logging_config_dict(filepath: Path | str) -> dict[str, Any]:
    """Load a logging config file and return as a dict"""
    config_dict = load_config_dict(filepath)
    return config_dict["log"]


def get_working_directory(config: Config | None = None) -> Path:
    """Get the working directory for `iostoolbox`.

    In order of precedence:
      - `IOSTOOLBOX_WORKING_DIR` environment variable
      - `working_directory` in `config.toml`
      - `~/.iostoolbox`
    """
    env_working_dir = os.getenv("IOSTOOLBOX_WORKING_DIR")
    if env_working_dir:
        working_directory = Path(env_working_dir)
    elif config and config.working_directory:
        working_directory = Path(config.working_directory)
    else:
        working_directory = Path.home() / ".iostoolbox"

    return working_directory.expanduser().resolve()
