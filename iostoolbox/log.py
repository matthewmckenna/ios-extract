import logging
import logging.config
from pathlib import Path

from .config import (
    get_default_config_filepath,
    get_project_directory,
    load_logging_config_dict,
)
from .dates_and_times import ymdhms_now
from .io import ensure_path


def setup_logging(
    logger_name: str | None = "dev", *, config_filepath: Path | None = None
) -> logging.Logger:
    """Configure logging"""
    project_directory = get_project_directory()

    if config_filepath is None:
        config_filepath = get_default_config_filepath()
    logging_config = load_logging_config_dict(config_filepath)

    timestamp = ymdhms_now()
    logs_directory = ensure_path(project_directory / "logs")
    logging_config["handlers"]["file_handler"]["filename"] = (
        logs_directory / f"{timestamp}.log"
    ).as_posix()

    logging.config.dictConfig(logging_config)
    return logging.getLogger(logger_name)
