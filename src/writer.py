#!/usr/bin/env python3
from pathlib import Path
import random
import json
from dataclasses import dataclass
from argparse import ArgumentParser

from PIL import Image, ImageDraw

from trimmer import trim_image

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
    result = layout(font, text)
    result = trim_image(result)
    result.save("out.png")


FontDict = dict[str, list[Image.Image]]


@dataclass
class BoundingBox:
    start_x: float
    end_x: float
    baseline_y: float


class Font:
    @staticmethod
    def load(text: str) -> "Font":
        letters_images = {}
        letters = set(text.replace(" ", "").replace("\n", ""))
        for letter in letters:
            letters_images[letter] = []
            filename = Font._char_to_filename(letter)
            for img in Path(f"../letters/ready/{filename}").glob("*.png"):
                letters_images[letter].append(Image.open(img))
            if not letters_images:
                print(f'Error: no images for letter "{letter}"')
                exit(1)
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
        with open("bounding-boxes.json") as f:
            self._bounding_boxes = json.load(f)

    def letter(self, char: str) -> Image.Image:
        return random.choice(self.dict[char])

    def bounding_box(self, char: str) -> BoundingBox:
        return BoundingBox(*self._bounding_boxes[char])

    def line_height(self) -> float:
        return max(
            map(
                lambda variations: max(
                    map(lambda variation: variation.height, variations)
                ),
                self.dict.values(),
            )
        )


def layout(font: Font, text: str) -> Image.Image:
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
    # breakpoint()
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
