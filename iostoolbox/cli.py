#!/usr/bin/env python
""""""
from pathlib import Path

import click

from . import __version__
from .log import setup_logging


@click.group()
@click.version_option(version=__version__)
def cli():
    """CLI tools for creating and working with an invoices database"""
    pass


config_option = click.option(
    "-c",
    "--config",
    "config_filepath",
    type=click.Path(resolve_path=True, path_type=Path, dir_okay=False),
    help="path to config file",
    default="./config.toml",
    show_default=True,
)

if __name__ == "__main__":
    cli()
