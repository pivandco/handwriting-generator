import json
import random
import sys
from logging import getLogger
from pathlib import Path

from PIL import Image

from .bbox import BoundingBox

Coordinates = tuple[int, int]
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
            for img in Path(f"font/ready/{filename}").glob("*.png"):
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
        with open("font/bounding-boxes.json", encoding="utf8") as bboxes_file:
            self._bounding_boxes = json.load(bboxes_file)

    def letter_variation(self, char: str) -> "LetterVariation":
        """Returns a :class:`Letter` instance for character ``char``."""
        return LetterVariation(
            char,
            random.choice(self.dict[char]),
            BoundingBox(**self._bounding_boxes[char]),
        )

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


class LetterVariation:
    """
    Provides access to a letter variation image and its dimensions
    (bounding boxes, connection points).
    """

    def __init__(self, char: str, image: Image.Image, bbox: BoundingBox):
        self.char = char
        self.image = image
        self.bbox = bbox
        self._logger = getLogger("writer.LetterVariation")

    def find_connection_start_coords(self) -> Coordinates:
        """
        Returns the starting coordinates of an inter-letter connection
        (this letter is the first in the connected pair).
        """
        if not self.char.isalpha():
            raise InvalidLetterInterconnectionError(
                "inter-letter connections between non-alphabetic characters does not make sense"
            )

        # TODO: start at baseline
        far_right_vertical_slice = (
            self.image.crop(
                (self.image.width - 1, 0, self.image.width, self.image.height)
            )
            .getchannel("L")
            .getdata()
        )
        try:
            connection_y = list(far_right_vertical_slice).index(0)
        except ValueError:
            self._logger.warning(
                "Failed to find the Y starting connection coordinate for %s: "
                "far right slice does not have black pixels",
                repr(self),
            )
            connection_y = int(self.image.height / 2)
        return self.image.width, connection_y

    def find_connection_end_coords(self) -> Coordinates:
        """
        Returns the ending coordinates of an inter-letter connection
        (this letter is the last in the connected pair).
        """
        if not self.char.isalpha():
            raise InvalidLetterInterconnectionError(
                "inter-letter connections between non-alphabetic characters does not make sense"
            )

        part_above_baseline = self.image.crop(
            (0, 0, self.image.width, int(self.bbox.baseline_y * self.image.height))
        )
        part_above_baseline = part_above_baseline.crop(part_above_baseline.getbbox())
        far_left_vertical_slice = (
            part_above_baseline.crop((0, 0, 1, part_above_baseline.height))
            .getchannel("L")
            .getdata()
        )
        try:
            connection_y = list(far_left_vertical_slice).index(0)
        except ValueError:
            self._logger.warning(
                "Failed to find the Y ending connection coordinate for %s: "
                "far left slice does not have black pixels",
                repr(self),
            )
            connection_y = int(self.image.height / 2)
        return 0, connection_y

    def __repr__(self) -> str:
        return f"<LetterVariation src={self.image.filename!r}>"  # type: ignore


class InvalidLetterInterconnectionError(Exception):
    """
    Raised when an attempt to interconnect a non-alphabetical letter is made
    (calling :meth:`LetterVariation.find_connection_start_coords`
    or :meth:`LetterVariation.find_connection_end_coords` with digits and punctuation symbols).
    """
