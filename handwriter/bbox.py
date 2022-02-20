from dataclasses import dataclass
from enum import Enum
from json import JSONDecoder


class ConnectionStart(Enum):
    """Connection start calculation algorithm type."""

    FAR_RIGHT = "far_right"
    FAR_RIGHT_OF_BOTTOM_HALF = "far_right_of_bottom_half"
    BOTTOM = "bottom"


@dataclass
class BoundingBox:
    """
    Letter bounding box which provides information about how a letter should be positioned
    relatively to sibling letters and the current line.
    """

    start_x: float
    end_x: float
    baseline_y: float
    connection_start: ConnectionStart | None


class BoundingBoxesJSONDecoder(JSONDecoder):
    """
    JSON decoder which turns ``connection_start`` values
    into :class:`ConnectionStart` enum members.
    """

    def decode(self, s):  # pylint: disable=arguments-differ
        decoded = super().decode(s)
        return {
            letter: {
                **data,
                "connection_start": ConnectionStart(data["connection_start"])
                if "connection_start" in data
                else None,
            }
            for letter, data in decoded.items()
        }
