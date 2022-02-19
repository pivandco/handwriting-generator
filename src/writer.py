#!/usr/bin/env python3
import json
import random
import sys
from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from fontmaker.cropper import crop_image


def main():
    argp = ArgumentParser()
    argp.add_argument("textfile", type=open)
    argp.add_argument("-d", "--debug", action="store_true")
    args = argp.parse_args()

    text = args.textfile.read().replace("ё", "е").replace("Ё", "Е")
    font = Font.load(text)
    result = draw(font, text, args.debug)
    result = crop_image(result)
    result.save("out.png")


@dataclass
class BoundingBox:
    """
    Letter bounding box which provides information about how a letter should be positioned
    relatively to sibling letters and the current line.
    """

    start_x: float
    end_x: float
    baseline_y: float


FontDict = dict[str, list[Image.Image]]


class Font:
    """Provides access to letter images, their bounding boxes and line heights."""

    @staticmethod
    def load(text: str) -> "Font":
        """
        Loads the letter images from ``letters/ready``. Only those letters
        which are required for drawing ``text`` are loaded.
        """
        letters_images: FontDict = {}
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
        with open("bounding-boxes.json", encoding="utf8") as bboxes_file:
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


@dataclass
class DrawingContext:
    """
    Provides everything required for drawing handwritten text: canvas,
    cursor and baseline coordinates, a :class:`Font` instance.
    """

    canvas: Image.Image
    debug_drawer: ImageDraw.ImageDraw | None
    cursor_x = 100
    cursor_y = 100
    baseline_y: int | None = field(default=None, init=False)


def draw(font: Font, text: str, debug=False) -> Image.Image:
    """Draws the ``text`` using the ``font``."""
    canvas = Image.new(
        "RGBA",
        _estimate_biggest_canvas_size(font, text),
        _get_canvas_bg(debug),
    )
    debug_drawer = ImageDraw.Draw(canvas)
    context = DrawingContext(canvas, debug_drawer)

    for char_n, char in enumerate(text):
        _draw_char(context, char, char_n, font, canvas, debug, debug_drawer)

    return canvas


def _draw_char(
    context,
    char,
    char_n,
    font,
    canvas,
    debug,
    debug_drawer,
):
    if char == " ":
        context.cursor_x += 60
        return
    if char == "\n":
        context.cursor_x = 100
        context.cursor_y += font.line_height()
        context.baseline_y = None
        return

    letter = font.letter(char)
    bbox = font.bounding_box(char)
    start_x, start_y = _get_letter_start_coords(context, letter, bbox)
    width = letter.width * (bbox.end_x - bbox.start_x)

    canvas.paste(
        letter,
        (
            round(start_x),
            round(start_y),
        ),
        letter.convert("RGBA"),
    )

    if debug:
        _draw_debug_lines(canvas, debug_drawer, char_n, letter, bbox, start_x, start_y)

    context.cursor_x += width


def _get_letter_start_coords(context, letter, bbox):
    start_x = context.cursor_x - bbox.start_x * letter.width
    if context.baseline_y is None:
        context.baseline_y = context.cursor_y + bbox.baseline_y * letter.height
    start_y = context.baseline_y - letter.height * bbox.baseline_y
    return start_x, start_y


def _draw_debug_lines(canvas, debug_drawer, char_n, letter, bbox, start_x, start_y):
    end_x = start_x + letter.width * bbox.end_x
    end_y = start_y + letter.height
    if char_n == 0:
        debug_drawer.line([0, end_y, canvas.width, end_y], "red")
    debug_drawer.line([end_x, end_y, end_x, end_y - letter.height], "red")
    debug_drawer.line([start_x, end_y, start_x, end_y - letter.height], "blue")
    debug_drawer.line([start_x, end_y, end_x, end_y], "blue")


def _get_canvas_bg(debug):
    return (255, 255, 255, 255 if debug else 0)


def _estimate_biggest_canvas_size(font: Font, text: str) -> tuple[int, int]:
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
    return int(max_canvas_width + 200), int(max_canvas_height * 2 + 200)


if __name__ == "__main__":
    main()
