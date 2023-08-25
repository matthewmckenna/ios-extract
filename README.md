# iOS Toolbox

Utilities to extract and work with databases from an unencrypted iOS backup.

## Installation v2

This project is built with **Python 3.11.2**.

The project can be installed by running:

```zsh
❯ git clone git@github.com:matthewmckenna/ios-extract.git iostoolbox
❯ cd iostoolbox
❯ make install
```

This will do the following:

- Clone the repository into local directory `iostoolbox`
- Change directory into the newly cloned repository
- Remove any existing virtual environment (in `.venv`) if it exists
- Create a new virtual environment using Python 3.11.2
- Updates `pip` and `setuptools`
- Installs the `iostoolbox` project in editable mode

## Usage

```zsh
❯ iostoolbox --help
usage: iostoolbox [-h] [-o OUTPUT_DIRECTORY] [-n] [-s] [-v] [-w]

Extract specific files from an unencrypted iOS backup

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        output directory to extract the files to (default: None)
  -n, --dry-run         dry run & do not copy files (default: False)
  -s, --summarise       summarise all backup directorys in given path (default: False)
  -v, --version         print the version and exit (default: False)
  -w, --write-info-txt  write an info.txt file in the output directory (default: False)
```

### Create a backup & write an `info.txt` file

This command creates a backup in the default backup directory.

```zsh
❯ iostoolbox --write-info-txt
```

The backup created will be created in a timestamped subdirectory, e.g., `~/ios-backups/YYYYMMDD_HHMMSS`.
This backup directory can be changed via config file (`config.toml`) with the `output_directory` configuration parameter.

```toml
[iostoolbox]
output_directory = "~/ios-backups"
```

## TODO

- [ ] Last backup date: time is two hours behind. issue with timezones
- [ ] Explicitly write `UTC` to `info.txt` file
- [ ] Support loading YAML in `iostoolbox.config.load_config_dict()`

```txt
Last Backup Date: 2023-05-10 22:16:47
```

`iostoolbox --help` works.
## Example: Extract files from a backup

```zsh
❯ iostoolbox --write-info-txt
```

The databases are extracted to: `~/ios-backups/YYYYMMDD_HHMMSS`

```zsh
❯ ls ~/ios-backups/YYYYMMDD_HHMMSS
AddressBook.sqlite	ChatStorage.sqlite	info.txt		sms.db
```
