#!/usr/bin/env python3
from argparse import ArgumentParser
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from fontmaker.cropper import crop_image

from .bbox import BoundingBox
from .font import Font


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
class DrawingContext:
    """
    Provides everything required for drawing handwritten text: canvas,
    cursor and baseline coordinates, a :class:`Font` instance and a debug drawer.
    """

    canvas: Image.Image
    font: Font
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
    debug_drawer = ImageDraw.Draw(canvas) if debug else None
    context = DrawingContext(canvas, font, debug_drawer)

    for char_n, char in enumerate(text):
        _draw_char(context, char, char_n)

    return canvas


Coordinates = tuple[int, int]


def _draw_char(
    context: DrawingContext,
    char: str,
    char_n: int,
):
    if char == " ":
        context.cursor_x += 60
        return
    if char == "\n":
        context.cursor_x = 100
        context.cursor_y += context.font.line_height()
        context.baseline_y = None
        return

    letter = context.font.letter(char)
    bbox = context.font.bounding_box(char)
    start_x, start_y = start_coords = _get_letter_start_coords(context, letter, bbox)
    width = int(letter.width * (bbox.end_x - bbox.start_x))

    context.canvas.paste(
        letter,
        (
            round(start_x),
            round(start_y),
        ),
        letter.convert("RGBA"),
    )

    if context.debug_drawer:
        _draw_debug_lines(context, char_n, letter, bbox, start_coords)

    context.cursor_x += width


def _get_letter_start_coords(
    context: DrawingContext, letter: Image.Image, bbox: BoundingBox
) -> Coordinates:
    start_x = context.cursor_x - bbox.start_x * letter.width
    if context.baseline_y is None:
        context.baseline_y = int(context.cursor_y + bbox.baseline_y * letter.height)
    start_y = context.baseline_y - letter.height * bbox.baseline_y
    return int(start_x), int(start_y)


def _draw_debug_lines(
    context: DrawingContext,
    char_n: int,
    letter: Image.Image,
    bbox: BoundingBox,
    start_coords: Coordinates,
):
    debug_drawer = context.debug_drawer
    if not debug_drawer:
        return
    canvas = context.canvas
    start_x, start_y = start_coords

    end_x = start_x + letter.width * bbox.end_x
    end_y = start_y + letter.height
    if char_n == 0:
        debug_drawer.line([0, end_y, canvas.width, end_y], "red")
    debug_drawer.line([end_x, end_y, end_x, end_y - letter.height], "red")
    debug_drawer.line([start_x, end_y, start_x, end_y - letter.height], "blue")
    debug_drawer.line([start_x, end_y, end_x, end_y], "blue")


def _get_canvas_bg(debug: bool):
    return (255, 255, 255, 255 if debug else 0)


def _estimate_biggest_canvas_size(font: Font, text: str) -> Coordinates:
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
