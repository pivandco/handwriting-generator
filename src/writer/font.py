import json
import random
import sys
from pathlib import Path

from PIL import Image

from .bbox import BoundingBox

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

    def line_height(self) -> int:
        """Calculates the line height so that any possible line of text would fit."""
        return max(
            map(
                lambda variations: max(
                    map(lambda variation: variation.height, variations)
                ),
                self.dict.values(),
            )
        )
