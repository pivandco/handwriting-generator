from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from .font import Coordinates, Font, InvalidLetterInterconnectionError, LetterVariation


@dataclass
class DrawingContext:
    """
    Provides everything required for drawing handwritten text: canvas,
    cursor and baseline coordinates, a :class:`Font` instance and a debug drawer.
    """

    canvas: Image.Image
    font: Font
    drawer: ImageDraw.ImageDraw
    debug: bool
    cursor = [100, 100]
    baseline_y: int | None = field(default=None, init=False)
    connection_start: Coordinates | None = field(default=None, init=False)

    def insert_space(self):
        """
        Inserts a space, moving the cursor X position to the right
        and resetting the connection start coordinates.
        """
        self.cursor[0] += 60
        self.connection_start = None

    def insert_newline(self):
        """
        Inserts a line break, resetting the cursor X position and advancing the Y position,
        also resetting the baseline Y.
        """
        self.cursor[0] = 100
        self.cursor[1] += self.font.line_height()
        self.baseline_y = None
        self.connection_start = None


def draw(font: Font, text: str, debug=False) -> Image.Image:
    """Draws the ``text`` using the ``font``."""
    canvas = Image.new(
        "RGBA",
        _estimate_biggest_canvas_size(font, text),
        _get_canvas_bg(debug),
    )
    drawer = ImageDraw.Draw(canvas)
    context = DrawingContext(canvas, font, drawer, debug)

    for char_n, char in enumerate(text):
        _draw_char(context, char, char_n)

    return canvas


def _draw_char(
    context: DrawingContext,
    char: str,
    char_n: int,
):
    if char == " ":
        context.insert_space()
        return
    if char == "\n":
        context.insert_newline()
        return

    variation = context.font.letter_variation(char)
    start_x, start_y = start_coords = _get_variation_start_coords(context, variation)
    width = int(variation.image.width * (variation.bbox.end_x - variation.bbox.start_x))

    context.canvas.paste(
        variation.image,
        (
            round(start_x),
            round(start_y),
        ),
        variation.image.convert("RGBA"),
    )

    if context.debug:
        _draw_debug_lines(context, char_n, variation, start_coords)

    context.cursor[0] += width
    try:
        if context.connection_start is not None:
            context.drawer.line(
                context.connection_start
                + _add_coords(
                    variation.find_connection_end_coords(),
                    (start_x, start_y),
                ),
                "red",
                2,
            )
        context.connection_start = _add_coords(
            variation.find_connection_start_coords(),
            (start_x, start_y),
        )
    except InvalidLetterInterconnectionError:
        context.connection_start = None


def _add_coords(i: Coordinates, j: Coordinates) -> Coordinates:
    return (i[0] + j[0], i[1] + j[1])


def _get_variation_start_coords(
    context: DrawingContext, variation: LetterVariation
) -> Coordinates:
    bbox = variation.bbox
    img = variation.image
    start_x = context.cursor[0] - bbox.start_x * img.width
    if context.baseline_y is None:
        context.baseline_y = int(context.cursor[1] + bbox.baseline_y * img.height)
    start_y = context.baseline_y - img.height * bbox.baseline_y
    return int(start_x), int(start_y)


def _draw_debug_lines(
    context: DrawingContext,
    char_n: int,
    variation: LetterVariation,
    start_coords: Coordinates,
):
    drawer = context.drawer
    canvas = context.canvas
    start_x, start_y = start_coords
    bbox = variation.bbox
    img = variation.image

    end_x = start_x + img.width * bbox.end_x
    end_y = start_y + img.height
    if char_n == 0:
        drawer.line([0, end_y, canvas.width, end_y], "red")
    drawer.line([end_x, end_y, end_x, end_y - img.height], "red")
    drawer.line([start_x, end_y, start_x, end_y - img.height], "blue")
    drawer.line([start_x, end_y, end_x, end_y], "blue")


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
