#!/usr/bin/env python3
import os
from pathlib import Path
import shutil

from PIL import Image
from tqdm import tqdm

SOURCE_DIR = "../letters/transparent/"
DEST_DIR = "../letters/chopped/"


def chop():
    try:
        os.mkdir(DEST_DIR)
    except FileExistsError:
        pass
    for p in Path(DEST_DIR).glob('*'):
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

    source_files = list(Path(SOURCE_DIR).glob("*.png"))

    for src in tqdm(source_files):
        letter_dest_dir_path = Path(DEST_DIR) / src.stem
        max_width = 200 if src.stem.startswith('_') else 120
        letter_dest_dir_path.mkdir(exist_ok=True)
        src_img = Image.open(src)
        letter_ongoing = False
        letter_start_x = 0
        letter_n = 1
        for x in range(0, src_img.width + 1):
            potential_gap = src_img.crop((x, 0, x + 10, src_img.height))
            colors = potential_gap.getcolors()
            if not letter_ongoing and len(colors) > 1:
                letter_ongoing = True
                letter_start_x = x
            if letter_ongoing and len(colors) == 1:
                letter_ongoing = False
                if 20 < x - letter_start_x < max_width:
                    letter = src_img.crop((letter_start_x, 0, x, src_img.height))
                    letter.save(letter_dest_dir_path / f"{letter_n}.png")
                    letter_n += 1
        if letter_ongoing and 20 < src_img.width - letter_start_x < max_width:
            letter = src_img.crop((letter_start_x, 0, src_img.width, src_img.height))
            letter.save(letter_dest_dir_path / f"{letter_n}.png")
