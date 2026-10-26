"""Board geometry and scoring for the Viper Shot King bristle dartboard.

Board space is in millimetres with the origin at the centre of the bullseye,
+x to the right and +y straight up (towards the 20), as seen when facing the
board.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Clockwise from the top of the board.
SEGMENT_ORDER = (20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5)
SEGMENT_ANGLE_DEG = 360 / len(SEGMENT_ORDER)


@dataclass(frozen=True)
class BoardSpec:
    """Ring radii (mm, measured from the centre to the outside edge of each wire).

    The defaults are the regulation WDF dimensions the Viper Shot King is
    built to. If a measurement off the physical board disagrees, override the
    field rather than editing the defaults.
    """

    inner_bull_radius: float = 6.35  # 12.7 mm diameter double bull
    outer_bull_radius: float = 15.9  # 31.8 mm diameter single bull
    treble_inner_radius: float = 99.0
    treble_outer_radius: float = 107.0
    double_inner_radius: float = 162.0
    double_outer_radius: float = 170.0
    board_radius: float = 225.5  # 451 mm (17.75") playing surface


VIPER_SHOT_KING = BoardSpec()


@dataclass(frozen=True)
class Score:
    segment: int  # 1-20, 25 for the bull, 0 for a miss
    multiplier: int  # 0 (miss), 1, 2 or 3

    @property
    def value(self) -> int:
        return self.segment * self.multiplier

    @property
    def label(self) -> str:
        if self.multiplier == 0:
            return "MISS"
        if self.segment == 25:
            return "BULL" if self.multiplier == 2 else "25"
        return {1: "S", 2: "D", 3: "T"}[self.multiplier] + str(self.segment)


def segment_at_angle(angle_deg: float) -> int:
    """Number for a clockwise angle from straight up (0 deg = middle of the 20)."""
    index = int(((angle_deg + SEGMENT_ANGLE_DEG / 2) % 360) // SEGMENT_ANGLE_DEG)
    return SEGMENT_ORDER[index]


def score_from_point(x_mm: float, y_mm: float, spec: BoardSpec = VIPER_SHOT_KING) -> Score:
    radius = math.hypot(x_mm, y_mm)

    if radius <= spec.inner_bull_radius:
        return Score(25, 2)
    if radius <= spec.outer_bull_radius:
        return Score(25, 1)
    if radius > spec.double_outer_radius:
        return Score(0, 0)

    segment = segment_at_angle(math.degrees(math.atan2(x_mm, y_mm)))

    if spec.treble_inner_radius < radius <= spec.treble_outer_radius:
        return Score(segment, 3)
    if spec.double_inner_radius < radius:
        return Score(segment, 2)
    return Score(segment, 1)
