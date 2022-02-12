#!/usr/bin/env python3
import os
from pathlib import Path
from PIL import Image
import shutil
import numpy as np
from tqdm import tqdm

SOURCE_DIR = "../letters/bnw/"
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

letter_n = 1
for src in tqdm(sources):
    src_img = Image.open(src).convert("LA")
    x = np.asarray(src_img.convert('RGBA')).copy()
    x[:, :, 3] = (255 * (x[:, :, :3] < 128).any(axis=2)).astype(np.uint8)
    Image.fromarray(x).save(Path(DEST_DIR) / (src.stem + ".png"))
