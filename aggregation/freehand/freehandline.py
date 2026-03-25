import numpy as np
from dataclasses import dataclass

@dataclass
class FreehandLine:
    """A freehand line drawn on a Zooniverse subject image.

    :param subject_id: Zooniverse subject ID the line was drawn on.
    :type subject_id: int
    :param points: (N, 2) array of (x, y) coordinates along the line.
    :type points: numpy.ndarray
    """

    subject_id: int
    points: np.ndarray


@dataclass
class ExtractFreehandLine(FreehandLine):
    """A single freehand line from one volunteer's classification.

    :param classification_id: Zooniverse classification ID this line came from.
    :type classification_id: int
    """

    classification_id: int


@dataclass
class ClusterFreehandLine(FreehandLine):
    """A consensus line produced by clustering multiple volunteer extractions.

    ``points`` holds the representative line (first extract after direction
    alignment). ``extracts`` holds all contributing lines.

    :param extracts: All :class:`ExtractFreehandLine` objects that were grouped
        into this cluster.
    :type extracts: list[ExtractFreehandLine]
    """

    extracts: list[ExtractFreehandLine]
