#!/usr/bin/env python3
import os
from pathlib import Path
import shutil

from PIL import Image
import numpy as np
from tqdm import tqdm

SOURCE_DIR = "../letters/src/"
DEST_DIR = "../letters/transparent/"

try:
    os.mkdir(DEST_DIR)
except FileExistsError:
    pass
for p in Path(DEST_DIR).glob("*"):
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()

sources = list(Path(SOURCE_DIR).glob("*.jpg"))

for src in tqdm(sources):
    src_img = Image.open(src).convert("LA")
    pixels = np.asarray(src_img)
    pixels[pixels[:, :, 0] > 255 * 0.8] = (255, 0)
    pixels[pixels[:, :, 0] <= 255 * 0.8] = (0, 255)
    Image.fromarray(pixels).save(Path(DEST_DIR) / (src.stem + ".png"))
