#!/usr/bin/env python3
"""Extract specific files from an unencrypted iOS backup"""
import configparser
import json
import logging
import os
import re
import shutil
from pathlib import Path
import plistlib
import sys
from typing import Dict, Iterable, Iterator, Union

from rich import print

from . import __version__
from .cli_args import CommandLineArguments, parse_args
from .dates_and_times import _datetime_to_ddmmmyyyy, _get_ymd_hms_timestamp
from .log import setup_logging
from .models import BackupInfo


def _get_directory_names(directory: Path) -> Iterator[str]:
    """Yield directory names within `directory`"""
    for entry in os.scandir(directory):
        if entry.is_dir():
            yield entry.name


def load_config(filename: str) -> Dict[str, str]:
    """Load default settings from a configuration file."""
    cfg = configparser.ConfigParser()  # configparser.ConfigParser
    cfg.read(filename)
    return dict(cfg["defaults"])  # configparser.SectionProxy


def get_platform_backup_location() -> Path:
    """Return the platform-specific iOS backup location"""
    if sys.platform == "win32":
        backup_location = Path("~/AppData/Roaming/Apple Computer/MobileSync/Backup")
    elif sys.platform == "darwin":
        backup_location = Path("~/Library/Application Support/MobileSync/Backup")
    else:
        raise RuntimeError(f"{sys.platform} is not yet supported. Exiting")
    return backup_location.expanduser()


def get_backup_location(config: Dict[str, str]) -> Path:
    """Get the location of the iOS backups.

    Attempt to get the iOS backup location from the configuration file.
    If no backup location is specified, then fall-back to the default
    platform backup location.
    """
    # backups are stored in different locations on Windows and macOS
    # set the correct location for the platform
    if not config.get("backup_directory"):
        return get_platform_backup_location()
    else:
        return Path(config.get("backup_directory")).expanduser()


def get_backup_directory_interactive(
    backup_location: Path, logger: logging.Logger
) -> Path:
    """Choose a directory to extract files from."""
    choices = _build_backup_directory_options(backup_location)
    summarise_platform_backup_directories(backup_location, logger)
    return get_user_backup_directory_selection(choices)


def _build_backup_directory_options(base_backup_directory: Path) -> Dict[str, Path]:
    """Return a mapping from choice number to a path to the backup directory.

    Returns
    -------
    dict mapping from user input choice number to the path to the backup directory
    e.g,
    {
        1: PosixPath("/Users/user/Library/Application Support/MobileSync/Backup/46063E61-DC9F-40A2-888A-880FD5BA596A"),
        2: PosixPath("/Users/user/Library/Application Support/MobileSync/Backup/8A8269F1-BFC9-4828-9831-9A1ECD484F8C"),
    }
    """
    return {
        idx: base_backup_directory / directory_name
        for idx, directory_name in enumerate(
            _get_directory_names(base_backup_directory), start=1
        )
    }


def summarise_platform_backup_directories(
    backup_location: Path, logger: logging.Logger
):
    backup_directories = _build_backup_directory_options(backup_location)
    num_header_characters = 69
    print(f"[bold blue]{' Backups Available ':=^{num_header_characters}}[/]")
    for choice, backup_directory in backup_directories.items():
        get_backup_directory_info(backup_directory, choice, logger)
    print(f"[bold blue]{'':=^{num_header_characters}}[/]")


def get_target_backup_directory(
    backup_location: Path, config: Dict[str, str], logger: logging.Logger
) -> Path:
    """Get the target backup directory to extract database files from.

    Check the config file for a UUID set there.
    If no UUID is set in the config, then list available backups
    and interactively prompt user to select a directory.

    Parameters
    ----------
    backup_location: the location of the iOS backups
    config: dict containing key-value pairs from the configuration file

    Returns
    -------
    a Path instance to the target backup directory
    """
    device_uuid = config.get("uuid")
    if device_uuid is None:
        return get_backup_directory_interactive(backup_location, logger)
    return backup_location / device_uuid


def ensure_path(path: Path | str) -> Path:
    if isinstance(path, str):
        path = Path(path)
    path.mkdir(exist_ok=True, parents=True)
    return path


def get_backup_info(
    backup_location: Path, args: CommandLineArguments, cfg, logger: logging.Logger
) -> BackupInfo:
    """Get a BackupInfo instance with information about the selected backup.

    Parameters
    -----------
    backup_location: location of the iOS backups
    base_output_directory: base output directory
    config: dict with configuration parameters

    Returns
    -------
    BackupInfo instance
    """
    target_backup_directory = get_target_backup_directory(backup_location, cfg, logger)
    plist_backup_info = read_information_from_info_plist(target_backup_directory, logger)
    output_directory = get_output_directory(args, cfg)
    return BackupInfo.from_dict(
        dict(
            backup_directory=target_backup_directory,
            output_directory=output_directory,
            **plist_backup_info,
        )
    )


def get_output_directory(args: CommandLineArguments, cfg: Dict[str, str]) -> Path:
    """Return the output directory for the current extraction.

    Command line arguments take preference over the config file.
    A new output directory with the current timestamp in the format YYYYMMDD_HHMMSS
    is created for the current extraction.
    """
    return ensure_path(
        (args.output_directory or cfg.get("output_directory"))
        / _get_ymd_hms_timestamp()
    )


def main(args: CommandLineArguments, logger: logging.Logger):
    """Main entry point for the utility"""
    # load user configuration settings
    cfg = load_config("ios.config")

    # get the location of the iOS backups
    backup_location = get_backup_location(cfg)

    # two modes of operation here
    # 1. we specify a backup_directory in the config file
    # 2. we use the system location

    # TODO: this could be extracted as a sub-command
    if args.summarise:
        summarise_platform_backup_directories(backup_location, logger)
        return

    backup_info = get_backup_info(backup_location, args, cfg, logger)
    if args.write_info_txt:
        # write some information about the source of the backup
        backup_info.write_info_txt()

    if not args.dry_run:
        logger.info(f"Extract databases to {backup_info.output_directory}")
        copy_files(backup_info, logger)
    remove_empty_dirs(
        backup_info.output_directory.parent, pattern=r"^\d{8}_\d{6}$", logger=logger
    )


def build_source_filename_pre_ios10(backup_directory: Path, hashed_name: str):
    """Copy files of interest from the source backup directory to the desitination.

    Prior to iOS 10 the backup databases were not organised by subdirectory,
    and must be handled differently.
    """
    return backup_directory / hashed_name


def build_source_filename_post_ios10(backup_directory: Path, hashed_name: str):
    """Copy files of interest from the source backup directory to the destination.

    From iOS 10.0 onwards databases are organised in directories by the first
    byte (two characters) of the hashes database name.
    e.g., database `7c7fba66680ef796b916b067077cc246adacf01d`
    is inside a directory named `7c`
    """
    return backup_directory / hashed_name[:2] / hashed_name


def copy_files(backup_info: BackupInfo, logger: logging.Logger) -> None:
    """Copy files to a backup directory"""
    databases = load_json("data/databases.json")

    for db_name, hashed_name in databases.items():
        if backup_info.major_ios_version > 9:
            src = build_source_filename_post_ios10(
                backup_info.backup_directory, hashed_name
            )
        elif backup_info.major_ios_version <= 9:
            src = build_source_filename_pre_ios10(
                backup_info.backup_directory, hashed_name
            )
        dst = backup_info.output_directory / db_name

        try:
            shutil.copy2(src, dst)
        except FileNotFoundError:
            # the file doesn't exist
            logger.info(f"Couldn't find source file for {db_name!r} -- skipping")
            continue


def load_json(filepath: Union[str, Path]) -> Dict[str, str]:
    """helper utility to load a json file"""
    with open(filepath, "rt") as f:
        data = json.load(f)
    return data


def get_user_backup_directory_selection(choices: Dict[int, Path]) -> str:
    """Return the backup directory selected by the user"""
    invalid_inputs = 0
    invalid = False
    max_choice = max(choices)

    while True:
        choice = input(
            "Enter a number corresponding to the backup directory from "
            f"1--{max_choice}, or 'x' to exit:\n"
        )

        # exit condition
        if choice.lower() == "x":
            exit_with_exit_code_and_message(
                exit_code=1, msg="Got `x`. Exiting with exit code {exit_code}."
            )

        try:
            choice = int(choice)
        except ValueError:
            # anything other than a number or "x" will increase the
            # `invalid_inputs` count & set the `invalid` flag
            invalid_inputs += 1
            invalid = True
            choice = -1

        # we've gotten a valid backup directory
        if 1 <= choice <= max_choice:
            # TODO: update the info in brackets to give a human-readable name
            print(f"\nYou've chosen backup directory #{choice} ({choices[choice]})")
            break
        else:
            # the choice is a number outside of the valid range
            # inside the conditional if `invalid` is False
            if not invalid:
                invalid_inputs += 1
            invalid = False

        if invalid_inputs >= 3:
            exit_with_exit_code_and_message(
                exit_code=2,
                msg="Too many invalid inputs. Exiting with exit code {exit_code}.",
            )

    return choices[choice]


def exit_with_exit_code_and_message(exit_code: int, msg: str):
    """Exit the application with `exit_code`, first printing a message"""
    print(msg.format(exit_code=exit_code))
    sys.exit(exit_code)


def load_info_plist_from_directory(
    directory: Path, logger: logging.Logger
) -> Dict[str, str]:
    """Load an `Info.plist` file"""
    plist_filename = directory / "Info.plist"

    # open & read the plist file
    try:
        with open(plist_filename, "rb") as f:
            pl = plistlib.load(f)
    except FileNotFoundError as e:
        logger.info(f"No `Info.plist` file found in {directory}")

    return pl


def get_backup_directory_info(
    directory: Path, choice: int, logger: logging.Logger
) -> None:
    """Print summary information about the backup directory"""
    pl = load_info_plist_from_directory(directory, logger)

    # basic information to display
    keys = [
        "Device Name",
        "Last Backup Date",
        "Product Name",
        "Product Version",
    ]

    # create some shorthand variables
    device_name = pl["Device Name"]
    product_version = pl["Product Version"]
    product_name = pl["Product Name"]
    # TODO: check the type of `last_backup_date` and convert to a datetime
    last_backup_date = pl["Last Backup Date"]

    print(
        f"{choice}: [bold yellow1]{device_name}[/] [white]\[[bold deep_pink2]{product_name}[/]] (iOS version: [bold green]{product_version}[/])"
    )
    print(
        f" - [italic white]Last backed up: [bold dark_orange]{_datetime_to_ddmmmyyyy(last_backup_date)}[/]"
    )
    print()


def read_information_from_info_plist(directory: Path, logger: logging.Logger) -> Dict[str, str]:
    """Retrieve backup information from `Info.plist` file"""
    pl = load_info_plist_from_directory(directory, logger)

    # use a list rather than a set to preserve order
    keys = [
        "Build Version",  # 19A346
        "Device Name",
        "Display Name",
        "GUID",
        "ICCID",
        "IMEI",
        "IMEI 2",
        # this value is in UTC, but does not specify that when written to file
        # TODO: modify this entry to specify UTC in the output `info.txt`
        "Last Backup Date",
        "MEID",
        "Phone Number",
        "Product Name",  # iPhone XR
        "Product Type",  # iPhone11,8
        "Product Version",  # iOS version
        "Serial Number",
        "Target Identifier",
        "Unique Identifier",  # UUID
    ]

    # use `.get` in case the key doesn"t exist in `pl`
    return {k: pl.get(k) for k in keys}


def get_matching_dirs(directory: Path, pattern: str) -> Iterable[os.DirEntry[str]]:
    """Yield matching directory names in `directory`"""
    # compile the directory name pattern as we'll be using it multiple times
    dirname_pattern = re.compile(f"{pattern}")

    with os.scandir(directory) as it:
        for entry in it:
            # we're only interested in directories
            if not entry.is_dir():
                continue

            # if the directory name matches `pattern` then yield this directory
            if dirname_pattern.match(entry.name):
                yield entry


def remove_empty_dirs(directory: Path, pattern: str, logger: logging.Logger) -> None:
    """Remove empty directories within `directory` which match the regex `pattern`"""
    for d in get_empty_dirs(directory, pattern):
        logger.info(f"Removing empty directory {d.name}")
        Path(d.path).rmdir()


def get_empty_dirs(directory: Path, pattern: str) -> Iterable[os.DirEntry[str]]:
    """Find empty directories within `directory`.

    Yields directories that match the regex `pattern` in `directory`.

    Args:
        directory: string the starting directory
        pattern: string regex e.g., "\\d{8}_{6}" (double-escaped here)
        would match the directory "20170719_161932".

    Yields:
        os.DirEntry objects for empty directories which match `pattern`.
    """
    for dir_entry in get_matching_dirs(directory, pattern=pattern):
        with os.scandir(dir_entry) as it:
            # try to get the next item in `dir_entry`
            try:
                next(it)
            except StopIteration:
                # if we hit a StopIteration then there are no items in the directory, and the directory is empty
                # yield this directory name
                yield dir_entry


def iostoolbox():
    logger = setup_logging()
    args = parse_args()
    if args.version:
        print(__version__)
    else:
        main(args, logger)


if __name__ == "__main__":
    iostoolbox()
