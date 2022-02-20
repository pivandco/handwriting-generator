import os
import shutil
from pathlib import Path


def prepare_destination_directory(dir_path: os.PathLike):
    """Creates the destination directory and cleans up its contents if it existed beforehand."""
    dir_path = Path(dir_path)
    dir_path.mkdir(exist_ok=True)
    for path in Path(dir_path).glob("*"):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
