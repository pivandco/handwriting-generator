#!/usr/bin/env python3
from pathlib import Path
import random
import json
from dataclasses import dataclass
from argparse import ArgumentParser
import sys

from PIL import Image, ImageDraw

from fontmaker.cropper import crop_image

DEBUG = False


def main():
    global DEBUG
    argp = ArgumentParser()
    argp.add_argument("textfile", type=open)
    argp.add_argument("-d", "--debug", action="store_true")
    args = argp.parse_args()

    DEBUG = args.debug
    text = args.textfile.read().replace("ё", "е").replace("Ё", "Е")
    font = Font.load(text)
    result = draw(font, text)
    result = crop_image(result)
    result.save("out.png")


FontDict = dict[str, list[Image.Image]]


@dataclass
class BoundingBox:
    """
    Letter bounding box which provides information about how a letter should be positioned
    relatively to sibling letters and the current line.
    """
    start_x: float
    end_x: float
    baseline_y: float


class Font:
    """Provides access to letter images, their bounding boxes and line heights."""

    @staticmethod
    def load(text: str) -> "Font":
        """
        Loads the letter images from ``letters/ready``. Only those letters
        which are required for drawing ``text`` are loaded.
        """
        letters_images = {}
        letters = set(text.replace(" ", "").replace("\n", ""))
        for letter in letters:
            letters_images[letter] = []
            filename = Font._char_to_filename(letter)
            for img in Path(f"../letters/ready/{filename}").glob("*.png"):
                letters_images[letter].append(Image.open(img))
            if not letters_images:
                print(f'Error: no images for letter "{letter}"')
                sys.exit(1)
        return Font(letters_images)

    @staticmethod
    def _char_to_filename(char: str) -> str:
        if char.islower() or char.isdigit():
            return char
        if char.isupper():
            return f"_{char.lower()}"
        return {
            ".": "dot",
            ",": "comma",
            ":": "colon",
            ";": "semicolon",
            "-": "dash",
            '"': "quoteopen",
            "!": "exclamation",
            "?": "question",
        }[char]

    def __init__(self, font_dict: FontDict):
        self.dict = font_dict
        with open("bounding-boxes.json", encoding='utf8') as bboxes_file:
            self._bounding_boxes = json.load(bboxes_file)

    def letter(self, char: str) -> Image.Image:
        """Returns a random letter variation for character ``char``."""
        return random.choice(self.dict[char])

    def bounding_box(self, char: str) -> BoundingBox:
        """Returns a :class:`BoundingBox` for character ``char``."""
        return BoundingBox(*self._bounding_boxes[char])

    def line_height(self) -> float:
        """Calculates the line height so that any possible line of text would fit."""
        return max(
            map(
                lambda variations: max(
                    map(lambda variation: variation.height, variations)
                ),
                self.dict.values(),
            )
        )


def draw(font: Font, text: str) -> Image.Image:
    """Draws the ``text`` using the ``font``."""
    canvas = Image.new(
        "RGBA",
        estimate_biggest_canvas_size(font, text),
        (255, 255, 255, 255 if DEBUG else 0),
    )
    debug_drawer = ImageDraw.Draw(canvas)

    cursor_x = 100
    cursor_y = 100
    baseline_y = None

    for char_n, char in enumerate(text):
        if char == " ":
            cursor_x += 60
            continue
        if char == "\n":
            cursor_x = 100
            cursor_y += font.line_height()
            baseline_y = None
            continue

        letter = font.letter(char)
        bbox = font.bounding_box(char)

        start_x = cursor_x - bbox.start_x * letter.width
        if baseline_y is None:
            baseline_y = cursor_y + bbox.baseline_y * letter.height
        start_y = baseline_y - letter.height * bbox.baseline_y
        width = letter.width * (bbox.end_x - bbox.start_x)

        canvas.paste(
            letter,
            (
                round(start_x),
                round(start_y),
            ),
            letter.convert("RGBA"),
        )

        if DEBUG:
            end_x = start_x + letter.width * bbox.end_x
            end_y = start_y + letter.height
            if char_n == 0:
                debug_drawer.line([0, end_y, canvas.width, end_y], "red")
            debug_drawer.line([end_x, end_y, end_x, end_y - letter.height], "red")
            debug_drawer.line([start_x, end_y, start_x, end_y - letter.height], "blue")
            debug_drawer.line([start_x, end_y, end_x, end_y], "blue")

        cursor_x += width

    return canvas


def estimate_biggest_canvas_size(font: Font, text: str) -> tuple[int, int]:
    """Estimates a canvas size so that it would fit the ``text`` written using the ``font``."""
    max_letter_widths = {
        letter: max(map(lambda variation: variation.width, variations))
        for letter, variations in font.dict.items()
    }
    max_canvas_width = max(
        sum(map(lambda char: max_letter_widths[char], line.replace(" ", "")))
        for line in text.split("\n")
    )
    max_canvas_height = font.line_height() * text.count("\n")
    return max_canvas_width + 200, max_canvas_height * 2 + 200


if __name__ == "__main__":
    main()
