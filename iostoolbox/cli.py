#!/usr/bin/env python
""""""
from pathlib import Path

import click

from . import __version__
# from .log import setup_logging


config_option = click.option(
    "-c",
    "--config",
    "config_filepath",
    type=click.Path(resolve_path=True, path_type=Path, dir_okay=False),
    help="path to config file",
    default="./config.toml",
    show_default=True,
)


@click.group()
@click.version_option(version=__version__)
def cli():
    """CLI tools for creating and working with an invoices database"""
    pass


@cli.command()
@config_option
def extract_files(config_filepath: Path):
    print(__version__)
    print(config_filepath)


if __name__ == "__main__":
    cli()
