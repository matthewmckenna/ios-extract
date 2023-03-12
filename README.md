# ios-extract

Utility to extract specific files from an unencrypted iOS backup.

## Environment Info

- Python version: `3.11.1`
- Environment name: `dev`

## Usage

```zsh
❯ python extract_files.py --help
usage: extract_files.py [-h] [-o OUTPUT_DIRECTORY] [-n] [-s] [-w]

Extract specific files from an unencrypted iOS backup

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        output directory to extract the files to (default: None)
  -n, --dry-run         dry run & do not copy files (default: False)
  -s, --summarise       summarise all backup directorys in given path (default: False)
  -w, --write-info-txt  write an info.txt file in the output directory (default: False)
```

### Create a backup

- Creates a backup in the default backup directory (`~/ios-backups/%YYYYmmdd_HHMMSS%`)

```zsh
python extract_files.py
```
