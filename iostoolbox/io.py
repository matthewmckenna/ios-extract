from pathlib import Path


def pathify(path: Path | str) -> Path:
    """Return an absolute Path object with the home directory expanded"""
    if isinstance(path, str):
        path = Path(path)
    return path.expanduser().resolve()
