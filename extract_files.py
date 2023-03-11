#!/usr/bin/env python3
"""Extract specific files from an unencrypted iOS backup"""
import configparser
from datetime import datetime
import json
import os
import re
import shutil
from pathlib import Path
import plistlib
import sys
from typing import Dict, Iterable, Iterator, Union

from cli_args import CommandLineArguments, parse_args
from dates_and_times import _datetime_to_ddmmmyyyy


def scantree(path: Path) -> Iterator[os.DirEntry[str]]:
    """Recursively yield `DirEntry` objects for given directory"""
    for entry in os.scandir(path):
        if entry.is_dir():
            yield from scantree(entry.path)
        else:
            yield entry


def _get_directory_names(directory: Path) -> Iterator[str]:
    """Yield directory names within `directory`"""
    for entry in os.scandir(directory):
        if entry.is_dir():
            yield entry.name


def load_config(filename: str):
    """Load default settings from a configuration file."""
    cfg = configparser.ConfigParser()
    cfg.read(filename)
    return cfg["defaults"]


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


def get_backup_directory_interactive(backup_location: Path) -> Path:
    """Choose a directory to extract files from."""
    choices = _build_backup_directory_options(backup_location)
    summarise_platform_backup_directories(backup_location)
    return get_user_backup_directory_selection(choices)


def _build_backup_directory_options(base_backup_directory: Path) -> Dict[str, Path]:
    return {
        idx: base_backup_directory / directory_name
        for idx, directory_name in enumerate(
            _get_directory_names(base_backup_directory), start=1
        )
    }


def summarise_platform_backup_directories(backup_location: Path):
    backup_directories = _build_backup_directory_options(backup_location)
    num_header_characters = 69
    print(f"{' Backups Available ':=^{num_header_characters}}")
    for choice, backup_directory in backup_directories.items():
        get_backup_directory_info(backup_directory, choice)
    print(f"{'':=^{num_header_characters}}")


def get_target_backup_directory(backup_location: Path, config: Dict[str, str]) -> Path:
    # we can configure a UUID in the config file to select a backup directory or
    # we can interactively pick one
    device_uuid = config.get("uuid")
    if device_uuid is None:
        return get_backup_directory_interactive(backup_location)
    return backup_location / device_uuid


def main(args: CommandLineArguments):
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
        summarise_platform_backup_directories(backup_location)
        return

    target_backup_directory = get_target_backup_directory(backup_location, cfg)

    # get a dict with information from `Info.plist`
    backup_info = read_information_from_info_plist(target_backup_directory)

    # get the output directory from the config file, or command-line args
    output_directory = args.output_directory or cfg.get("output_directory")

    # TODO: move / remove as we continue the refactor
    sys.exit(99)

    # if there is no output directory set, then application will exit
    # after printing out information above
    if output:
        # command line args takes precedence
        if args.output:
            base_output_dir = args.output
        else:
            base_output_dir = cfg_output

        base_output_dir = Path(base_output_dir).expanduser()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # TODO: too many output directory variables - sort this out
        output_dir = base_output_dir / timestamp

        # create the output directory if it doesn't exist
        output_dir.mkdir(parents=True)

        # tidy up empty directories here
        remove_empty_dirs(base_output_dir, pattern=r"^\d{8}_\d{6}$")

        if args.copy:
            # write some information about the source of the backup
            write_backup_information(backup_info, output_dir)

            # read_ios_below_10
            # NOTE: if iOS version < 10 then there are no folders, and
            # all files are at the top level.
            ios_version = int(backup_info["Product Version"].split(".")[0])

            databases = load_json("databases.json")
            # TODO: read from `database.json`
            for db_name, hashed_name in databases.items():

                if ios_version > 9:
                    # databases are organised in directories by
                    # the first byte (two characters) of the database
                    # e.g., database `7c7fba66680ef796b916b067077cc246adacf01d`
                    # is inside a directory named `7c`
                    subdir = hashed_name[:2]

                    # `backup_directory` is where we will copy from (source)
                    # `output_dir` is where we will copy to (destination)
                    folder = backup_directory / subdir
                    src_path = folder / hashed_name
                    dest_path = output_dir / db_name
                else:
                    src_path = backup_directory / hashed_name
                    dest_path = output_dir / db_name

                try:
                    shutil.copy2(src_path, dest_path)
                except FileNotFoundError:
                    # the file doesn't exist
                    pass


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


def get_backup_directories(directory: Path) -> Dict[int, Path]:
    """Get available backup directories within `directory`"""
    # TODO: we can probably use a list here -- no point using a dict with integer keys
    choices: Dict[int, str] = {}
    counter = 1

    with os.scandir(directory) as it:
        for entry in it:
            # only interested in directories
            if entry.is_dir():
                try:
                    choice = get_choice(directory / entry.name)
                # TODO: am I handling this correctly?
                except FileNotFoundError:
                    # no Info.plist file found
                    pass
                else:
                    print(f"{counter}: {entry.name}")
                    choices[counter] = Path(entry.name)
                    counter += 1

    return choices


def load_info_plist_from_directory(directory: Path) -> Dict[str, str]:
    """Load an `Info.plist` file"""
    plist_filename = directory / "Info.plist"

    # open & read the plist file
    try:
        with open(plist_filename, "rb") as f:
            pl = plistlib.load(f)
    except FileNotFoundError as e:
        print(f"No `Info.plist` file found in {directory}")

    return pl


def get_backup_directory_info(directory: Path, choice: int) -> None:
    """Print summary information about the backup directory"""
    pl = load_info_plist_from_directory(directory)

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
    last_backup_date = pl["Last Backup Date"]

    print(f"{choice}: {device_name} [{product_name}] (iOS version: {product_version})")
    print(f" - Last backed up: {_datetime_to_ddmmmyyyy(last_backup_date)}")
    print()


def read_information_from_info_plist(directory: Path) -> Dict[str, str]:
    """Retrieve backup information from `Info.plist` file"""
    pl = load_info_plist_from_directory(directory)

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


def write_backup_information(backup_info: Dict[str, str], directory: Path) -> None:
    """Write backup information to a text file."""
    filename = directory / "info.txt"

    with open(filename, "wt") as f:
        for k in backup_info:
            f.write(f"{k}: {backup_info[k]}\n")


def get_matching_dirs(directory: Path, pattern: str) -> Iterable[os.DirEntry[str]]:
    """Yield matching directory names in `directory`"""
    # compile the directory name pattern as we"ll be using it multiple times
    dirname_pattern = re.compile(f"{pattern}")

    with os.scandir(directory) as it:
        for entry in it:
            # we"re only interested in directories
            if not entry.is_dir():
                continue

            # if the directory name matches `pattern` then yield this directory
            if dirname_pattern.match(entry.name):
                yield entry


def remove_empty_dirs(directory: Path, pattern: str) -> None:
    """Remove empty directories within `directory` which match the regex `pattern`"""
    for d in get_empty_dirs(directory, pattern):
        print(f"DRY RUN: remove directory={d.name}")
        # os.rmdir(d.path)


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


if __name__ == "__main__":
    args = parse_args()
    main(args)
