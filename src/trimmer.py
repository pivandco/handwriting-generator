#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

from PIL import Image
from tqdm import tqdm

SOURCE_DIR = "../letters/chopped/"
DEST_DIR = "../letters/ready/"


def trim_image(img: Image.Image) -> Image.Image:
    content_start_x = 0
    content_end_x = img.width
    content_start_y = 0
    content_end_y = img.height
    for x in range(1, img.width):
        sample_strip = img.crop((x - 1, 0, x, img.height))
        colors = sample_strip.getcolors()
        if len(colors) > 1:
            content_start_x = x
            break
    for x in range(img.width, -1, -1):
        sample_strip = img.crop((x - 1, 0, x, img.height))
        colors = sample_strip.getcolors()
        if len(colors) > 1:
            content_end_x = x
            break
    for y in range(1, img.height):
        sample_strip = img.crop((0, y - 1, img.width, y))
        colors = sample_strip.getcolors()
        if len(colors) > 1:
            content_start_y = y
            break
    for y in range(img.height, -1, -1):
        sample_strip = img.crop((0, y - 1, img.width, y))
        colors = sample_strip.getcolors()
        if len(colors) > 1:
            content_end_y = y
            break

    return img.crop((content_start_x, content_start_y, content_end_x, content_end_y))


def trim():
    try:
        os.mkdir(DEST_DIR)
    except FileExistsError:
        pass
    for p in Path(DEST_DIR).glob("*"):
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

    source_dirs = list(Path(SOURCE_DIR).glob("*"))

    for src_dir in tqdm(source_dirs):
        letter_dest_dir_path = Path(DEST_DIR) / src_dir.name
        letter_dest_dir_path.mkdir(exist_ok=True, parents=True)
        letter_n = 1
        for src in src_dir.glob("*.png"):
            src_img = Image.open(src)
            letter = trim_image(src_img)
            letter.save(letter_dest_dir_path / f"{letter_n}.png")
            letter_n += 1


if __name__ == "__main__":
    trim()
