from pathlib import Path

import numpy as np
from PIL import Image
from tqdm import tqdm

from ._utils import prepare_destination_directory

SOURCE_DIR = "../letters/src/"
DEST_DIR = "../letters/transparent/"


def remove_background():
    """
    Makes letter variations series images black & white
    and makes white background transparent.
    """

    prepare_destination_directory(DEST_DIR)

    sources = list(Path(SOURCE_DIR).glob("*.jpg"))

    for src in tqdm(sources):
        src_img = Image.open(src).convert("LA")
        pixels = np.asarray(src_img)
        pixels[pixels[:, :, 0] > 255 * 0.8] = (255, 0)
        pixels[pixels[:, :, 0] <= 255 * 0.8] = (0, 255)
        Image.fromarray(pixels).save(Path(DEST_DIR) / (src.stem + ".png"))
