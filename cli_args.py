from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CommandLineArguments:
    dry_run: bool
    summarise: bool
    output_directory: Path | None = None

    def __post_init__(self):
        # set a default directory to store ios-backups
        # TODO: set this in a config file
        if self.output_directory is None:
            self.output_directory = Path.home() / "ios-backups"

        if isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)
        self.output_directory = self.output_directory.expanduser()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


def parse_args() -> CommandLineArguments:
    parser = argparse.ArgumentParser(
        description="Extract specific files from an unencrypted iOS backup",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="output directory",
        type=Path,
    )
    parser.add_argument(
        "-n", "--dry-run", help="dry run & do not copy files", action="store_true"
    )
    parser.add_argument(
        "-s",
        "--summarise",
        help="summarise all backup directorys in given path",
        action="store_true",
    )
    args = parser.parse_args()
    return CommandLineArguments(
        dry_run=args.dry_run,
        summarise=args.summarise,
        output_directory=args.output_directory,
    )
