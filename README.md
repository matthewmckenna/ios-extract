# ios-extract

Utility to extract specific files from an unencrypted iOS backup.

## Environment Info

- Python version: `3.11.1`
- Environment name: `dev`

## Usage

```zsh
❯ python extract_files.py --help
usage: extract_files.py [-h] [-o OUTPUT] [-c] [-s]

extract specific files from an unencrypted iOS backup

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output directory (default: None)
  -c, --copy            copy the database files (default: False)
  -s, --summarise       summarise all backup directorys in given path (default: False)
```

### Create a backup

- Creates a backup in the default backup directory (`~/ios-backups/%YYYYmmdd_HHMMSS%`)

```zsh
python extract_files.py --copy
```
