#!/usr/bin/env python3
"""utility to extract specific files from an unencrypted iOS backup"""
import argparse
import configparser
from datetime import datetime
import json
import os
import re
import shutil
from pathlib import Path
import plistlib
from pprint import pprint
import sys
from typing import Dict, Iterable, Union


def load_config(filename: str):
    """Load default settings from a configuration file."""
    cfg = configparser.ConfigParser()
    cfg.read(filename)
    return cfg['defaults']


def main(args):
    """main entry point for the script"""
    # load user configuration settings
    cfg = load_config('ios.config')

    # if we have specified a uuid then we don't want to summarise
    try:
        device_uuid = cfg['uuid']
    except KeyError:
        device_uuid = None

    # backups are stored in different locations on windows and macos
    if sys.platform == 'win32':
        platform_backup_loc = '~/AppData/Roaming/Apple Computer/MobileSync/Backup'
    elif sys.platform == 'darwin':
        platform_backup_loc = '~/Library/Application Support/MobileSync/Backup'

    backup_dir = Path(platform_backup_loc).expanduser()

    # TODO: why check if `device_uuid` is None here?
    # TODO: should we `.expanduser()` after getting the backup_dir
    # TODO: `backup_dir` must be a Path object
    if device_uuid is None:
        try:
            backup_dir = Path(cfg['backup_dir'])
        except KeyError:
            # no backup dir specified in the configuration file, so use
            # the platform locations
            pass

    # TODO: can I clean up the creation of `backup_directory`?
    if args.summarise:
        directory_choice = choose_backup_directory(backup_dir)
        backup_directory = backup_dir / directory_choice
    else:
        backup_directory = backup_dir / device_uuid

    # get a dict with information from `Info.plist`
    backup_info = get_backup_information(backup_directory)

    # get the output directory from the config file, or command-line args
    cfg_output = cfg.get('output_dir')

    # set a flag if either are set
    # TODO: this isn't a flag?
    output = args.output or cfg_output

    # if there is no output directory set, then application will exit
    # after printing out information above
    if output:
        # command line args takes precedence
        if args.output:
            base_output_dir = args.output
        else:
            base_output_dir = cfg_output

        base_output_dir = Path(base_output_dir).expanduser()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # TODO: too many output directory variables - sort this out
        output_dir = base_output_dir / timestamp

        # create the output directory if it doesn't exist
        output_dir.mkdir(parents=True)

        # tidy up empty directories here
        remove_empty_dirs(base_output_dir, pattern=r'^\d{8}_\d{6}$')

        if args.copy:
            # write some information about the source of the backup
            write_backup_information(backup_info, output_dir)

            # read_ios_below_10
            # NOTE: if iOS version < 10 then there are no folders, and
            # all files are at the top level.
            ios_version = int(backup_info['Product Version'].split('.')[0])

            databases = load_json('databases.json')
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
    with open(filepath, 'rt') as f:
        data = json.load(f)
    return data


def choose_backup_directory(backup_dir: Path) -> Path:
    """choose a backup directory to extract files from"""
    # TODO: check the logic around the `invalid` flag
    invalid_inputs = 0
    invalid = False
    choices = get_backup_choices(backup_dir)
    max_choice = max(choices.keys())

    while True:
        choice = input(
            "Enter a number corresponding to the backup directory from "
            f"1--{max_choice}, or 'x' to exit:\n"
        )

        if choice.lower() == 'x':
            # TODO: is there a cleaner way to exit the script?
            sys.exit()

        try:
            choice = int(choice)
        except ValueError:
            # anything other than a number or 'x' will increase the
            # `invalid_inputs` count & set the `invalid` flag
            invalid_inputs += 1
            invalid = True
            choice = -1

        if 1 <= choice <= max_choice:
            print(f'\nyou have chosen backup directory #{choice} ({choices[choice]})\n')
            break
        else:
            # if the number is outside of the valid range
            # inside the conditional if `invalid` is False
            if not invalid:
                invalid_inputs += 1
            invalid = False

        # TODO: check if this is the most graceful way to exit
        if invalid_inputs >= 3:
            print('Too many invalid inputs. Exiting.')
            sys.exit(1)

    return choices[choice]


def get_backup_choices(directory: Path) -> Dict[int, Path]:
    """get a list of choices for which iOS backup to examine."""
    choices = {}
    counter = 1

    with os.scandir(directory) as it:
        for entry in it:
            # only interested in directories
            if entry.is_dir():
                try:
                    get_summary_backup_info(directory / entry.name)
                # TODO: am I handling this correctly?
                except FileNotFoundError:
                    # no Info.plist file found
                    pass
                else:
                    print(f'{counter}: {entry.name}')
                    choices[counter] = Path(entry.name)
                    counter += 1

    return choices


def get_summary_backup_info(directory: Path):
    """print a summary of the backup directory"""
    plist_filename = directory / 'Info.plist'

    # read the plist file
    with open(plist_filename, 'rb') as f:
        pl = plistlib.load(f)

    # basic information to display
    keys = [
        'Device Name',
        'Last Backup Date',
        'Product Type',  # iPhone8,1
        'Product Name',  # iPhone XR
        'Product Version',  # iOS version
        'Unique Identifier',
    ]

    # create a dict with a reduced set of plist entries
    info = {k: pl[k] for k in keys}

    # print out some basic information
    pprint(info)


def get_backup_information(directory: Path) -> Dict[str, str]:
    """retrieve backup information from `Info.plist` file"""
    plist_filename = directory / 'Info.plist'

    with open(plist_filename, 'rb') as f:
        pl = plistlib.load(f)

    # use a list rather than a set to preserve order
    keys = [
        'Build Version',  # 19A346
        'Device Name',
        'Display Name',
        'GUID',
        'ICCID',
        'IMEI',
        'IMEI 2',
        'Last Backup Date',
        'MEID',
        'Phone Number',
        'Product Name',  # iPhone XR
        'Product Type',  # iPhone11,8
        'Product Version',  # iOS version
        'Serial Number',
        'Target Identifier',
        'Unique Identifier',  # uuid
    ]

    # use `.get` in case the key doesn't exist in `pl`
    return {k: pl.get(k) for k in keys}


def write_backup_information(backup_info: Dict[str, str], directory: Path) -> None:
    """write backup information to a file"""
    filename = directory / 'info.txt'

    with open(filename, 'w') as f:
        for k in backup_info:
            f.write(f'{k}: {backup_info[k]}\n')


def get_matching_dirs(directory: Path, pattern: str) -> Iterable[os.DirEntry[str]]:
    """yield matching directory names in `directory`"""
    # compile the directory name pattern
    dirname_pattern = re.compile(f'{pattern}')

    with os.scandir(directory) as it:
        for entry in it:
            # only interested in directories
            if not entry.is_dir():
                continue

            if dirname_pattern.match(entry.name):
                yield entry


def remove_empty_dirs(directory: Path, pattern: str) -> None:
    """remove empty directories within `directory` which match the regex `pattern`"""
    for d in get_empty_dirs(directory, pattern):
        print(f'DRY RUN: remove directory={d.name}')
        # os.rmdir(d.path)


def get_empty_dirs(directory: Path, pattern: str) -> Iterable[os.DirEntry[str]]:
    """get empty directories within `directory`.

    Yields directories that match the regex `pattern` in `directory`.

    Args:
        directory: string the starting directory
        pattern: string regex e.g., '\\d{8}_{6}' (double-escaped here)
        would match the directory '20170719_161932'.

    Yields:
        os.DirEntry objects for empty directories which match `pattern`.
    """
    for dir_entry in get_matching_dirs(directory, pattern=pattern):
        with os.scandir(dir_entry) as it:
            # try to get the next item in `dir_entry`
            try:
                next(it)
            except StopIteration:
                # if there is nothing, then the directory is empty
                # yield this directory name
                yield dir_entry


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='extract specific files from an unencrypted iOS backup',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-o', '--output', help='output directory')
    parser.add_argument('-c', '--copy', help='copy the database files', action='store_true')
    parser.add_argument(
        '-s',
        '--summarise',
        help='summarise all backup directorys in given path',
        action='store_true',
    )

    args = parser.parse_args()
    main(args)
