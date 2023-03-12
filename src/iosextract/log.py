from datetime import datetime, timezone
import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging(logger_name: str | None = "dev") -> logging.Logger:
    """Configure logging"""
    logs_directory = Path.cwd() / "logs"
    logs_directory.mkdir(exist_ok=True)

    config_filepath = Path.cwd() / "config" / "logging.yaml"
    with open(config_filepath, "rt") as f:
        config = yaml.safe_load(f.read())

    # update the log filepath
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    config["handlers"]["file_handler"]["filename"] = (
        logs_directory / f"{timestamp}.log"
    ).as_posix()

    logging.config.dictConfig(config)

    return logging.getLogger(logger_name)


if __name__ == "__main__":
    logger = setup_logging()
    logger.info("check info")
    logger.debug("check debug")
