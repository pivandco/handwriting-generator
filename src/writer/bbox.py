from dataclasses import dataclass


@dataclass
class BoundingBox:
    """
    Letter bounding box which provides information about how a letter should be positioned
    relatively to sibling letters and the current line.
    """

    start_x: float
    end_x: float
    baseline_y: float
    connect_at_baseline: bool = False
