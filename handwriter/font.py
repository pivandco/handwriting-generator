import json
import random
import sys
from logging import getLogger
from pathlib import Path

from PIL import Image

from .bbox import BoundingBox, BoundingBoxesJSONDecoder, ConnectionStart
from .config import CONFIG

Coordinates = tuple[int, int]
FontDict = dict[str, list[Image.Image]]


class Font:
    """Provides access to letter images, their bounding boxes and line heights."""

    @staticmethod
    def load(text: str) -> "Font":
        """
        Loads the letter images from ``font/ready``. Only those letters
        which are required for drawing ``text`` are loaded.
        """
        letters_images: FontDict = {}
        letters = set(text.replace(" ", "").replace("\n", ""))
        for letter in letters:
            letters_images[letter] = []
            filename = Font._char_to_filename(letter)
            for img in Path(f"{CONFIG['paths']['font']}/ready/{filename}").glob(
                "*.png"
            ):
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
        with open(
            f"{CONFIG['paths']['font']}/bounding-boxes.json", encoding="utf8"
        ) as bboxes_file:
            self._bounding_boxes = json.load(bboxes_file, cls=BoundingBoxesJSONDecoder)

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
                "letter interconnections between non-alphabetic characters does not make sense"
            )

        if self.bbox.connection_start == ConnectionStart.FAR_RIGHT:
            connection_x = self.image.width
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

        elif self.bbox.connection_start == ConnectionStart.BOTTOM:
            connection_y = self.image.height
            bottom_slice = (
                self.image.crop(
                    (0, self.image.height - 1, self.image.width, self.image.height)
                )
                .getchannel("L")
                .getdata()
            )
            try:
                connection_x = list(bottom_slice).index(0)
            except ValueError:
                self._logger.warning(
                    "Failed to find the X starting connection coordinate for %s: "
                    "bottom slice does not have black pixels",
                    repr(self),
                )
                connection_x = int(self.image.width / 2)

        elif self.bbox.connection_start == ConnectionStart.FAR_RIGHT_OF_BOTTOM_HALF:
            bottom_half = self.image.crop(
                (0, int(self.image.height / 2), self.image.width, self.image.height)
            )
            bottom_half_bbox = bottom_half.getbbox()
            assert bottom_half_bbox is not None
            connection_x = rightmost_nonempty_x = bottom_half_bbox[3]
            far_right_vertical_slice = (
                bottom_half.crop(
                    (
                        rightmost_nonempty_x - 1,
                        0,
                        rightmost_nonempty_x,
                        bottom_half.height,
                    )
                )
                .getchannel("L")
                .getdata()
            )
            try:
                connection_y = int(
                    self.image.height / 2 + list(far_right_vertical_slice).index(0)
                )
            except ValueError:
                self._logger.warning(
                    "Failed to find the Y starting connection coordinate for %s: "
                    "far right slice does not have black pixels",
                    repr(self),
                )
                connection_y = int(self.image.height / 2)

        return connection_x, connection_y

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
        part_above_baseline_bbox = part_above_baseline.getbbox()
        assert part_above_baseline_bbox is not None
        leftmost_nonempty_x = part_above_baseline_bbox[0]
        far_left_vertical_slice = (
            part_above_baseline.crop(
                (
                    leftmost_nonempty_x,
                    0,
                    leftmost_nonempty_x + 1,
                    part_above_baseline.height,
                )
            )
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
        return leftmost_nonempty_x, connection_y

    def __repr__(self) -> str:
        return f"<LetterVariation src={self.image.filename!r}>"  # type: ignore


class InvalidLetterInterconnectionError(Exception):
    """
    Raised when an attempt to interconnect a non-alphabetical letter is made
    (calling :meth:`LetterVariation.find_connection_start_coords`
    or :meth:`LetterVariation.find_connection_end_coords` with digits and punctuation symbols).
    """
