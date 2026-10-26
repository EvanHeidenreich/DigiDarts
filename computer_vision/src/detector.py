"""Find where a thrown dart lands by differencing against a reference frame.

The detector keeps a grayscale reference of the board as it looked before the
throw. When something moves (a dart arriving), it waits for the image to go
still again, then diffs the settled frame against the reference. The new dart
is the largest changed blob. The settled frame then becomes the new reference,
so each dart is isolated from the ones already in the board.

To tell the tip end of the blob from the flight end, the detector uses the
camera geometry when it's given it (the flight sticks out toward the camera),
and otherwise picks the end carrying less area, since the flight is the bulk
of the dart. The cleaned-up blob loses the thin steel point, so the tip is then
traced outward along the shaft through the raw difference pixels.

When the board goes back to looking like it did with no darts in it, or a
change much larger than a dart happens (a hand in front of the board), the
detector reports Cleared instead of a dart.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Tuple, Union

import cv2
import numpy as np

Point = Tuple[float, float]
# Given a pixel, the unit image direction from a dart's tip toward its flight
# there, or None if unknown (see BoardCalibration.out_of_board_direction).
FlightDirection = Callable[[Point], Optional[Point]]


class State(Enum):
    IDLE = "idle"
    MOTION = "motion"


@dataclass
class DetectorConfig:
    blur_kernel: int = 5
    diff_threshold: int = 25  # grey levels a pixel must change by to count
    motion_pixels: int = 300  # frame-to-frame changed pixels that count as movement
    settle_frames: int = 8  # still frames required before analysing
    min_dart_area: int = 150  # px; smaller blobs are noise
    max_dart_area: int = 25000  # px; larger changes are a hand / darts removed
    end_fraction: float = 1 / 3  # share of the blob length compared at each end for area
    min_direction_alignment: float = 0.3  # |cos| between shaft and flight direction needed to trust it
    tip_lateral_px: float = 5.0  # how far off the shaft line raw pixels may be to extend the tip
    tip_max_gap_px: int = 3  # gap in raw pixels along the shaft that ends the tip trace
    tip_max_extension: float = 0.5  # cap on the tip trace, as a share of the blob length

    # The pixel values above were tuned on this resolution.
    TUNED_SIZE = (960, 600)

    @classmethod
    def for_resolution(cls, width: int, height: int) -> "DetectorConfig":
        """Defaults with the pixel sizes and areas scaled to the camera resolution."""
        scale = math.sqrt(width * height / (cls.TUNED_SIZE[0] * cls.TUNED_SIZE[1]))
        base = cls()
        return cls(
            blur_kernel=max(3, int(round(base.blur_kernel * scale)) | 1),  # must stay odd
            motion_pixels=int(base.motion_pixels * scale**2),
            min_dart_area=int(base.min_dart_area * scale**2),
            max_dart_area=int(base.max_dart_area * scale**2),
            tip_lateral_px=base.tip_lateral_px * scale,
            tip_max_gap_px=max(1, int(round(base.tip_max_gap_px * scale))),
        )


@dataclass
class Dart:
    tip: Point
    contour: np.ndarray
    axis: Tuple[Point, Point]  # (tip end, flight end) along the fitted shaft line


@dataclass
class Cleared:
    changed_area: int


DetectorEvent = Union[Dart, Cleared]


class DartDetector:
    def __init__(self, config: DetectorConfig | None = None):
        self.config = config or DetectorConfig()
        self.state = State.IDLE
        self.reference: Optional[np.ndarray] = None
        self.empty_board: Optional[np.ndarray] = None
        self.last_mask: Optional[np.ndarray] = None
        self._previous: Optional[np.ndarray] = None
        self._still_count = 0

    def reset(self) -> None:
        """Take the next frame as the reference (e.g. after the board is emptied)."""
        self.reference = None
        self.empty_board = None
        self._previous = None
        self.state = State.IDLE
        self._still_count = 0

    def update(self, frame: np.ndarray, flight_direction: Optional[FlightDirection] = None) -> Optional[DetectorEvent]:
        gray = self._preprocess(frame)

        if self.reference is None:
            self.reference = gray
            self.empty_board = gray
            self._previous = gray
            return None

        motion = cv2.countNonZero(self._threshold(cv2.absdiff(gray, self._previous)))
        self._previous = gray

        if motion > self.config.motion_pixels:
            self.state = State.MOTION
            self._still_count = 0
            return None

        self._still_count += 1

        if self.state == State.IDLE:
            # Nothing is happening, so let the reference follow slow lighting drift.
            if self.empty_board is self.reference:
                self.empty_board = gray
            self.reference = gray
            return None

        if self._still_count < self.config.settle_frames:
            return None

        self.state = State.IDLE
        event = self._analyse(gray, flight_direction)
        if isinstance(event, Cleared):
            self.empty_board = gray
        self.reference = gray
        return event

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        k = self.config.blur_kernel
        return cv2.GaussianBlur(gray, (k, k), 0)

    def _threshold(self, diff: np.ndarray) -> np.ndarray:
        _, mask = cv2.threshold(diff, self.config.diff_threshold, 255, cv2.THRESH_BINARY)
        return mask

    def _change_mask(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        mask = self._threshold(cv2.absdiff(a, b))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    def _analyse(self, gray: np.ndarray, flight_direction: Optional[FlightDirection]) -> Optional[DetectorEvent]:
        mask = self._change_mask(gray, self.reference)
        self.last_mask = mask
        changed = cv2.countNonZero(mask)

        # Darts were in the board and now it matches the empty board again.
        if self.empty_board is not self.reference and changed >= self.config.min_dart_area:
            if cv2.countNonZero(self._change_mask(gray, self.empty_board)) < self.config.min_dart_area:
                return Cleared(changed)

        if changed > self.config.max_dart_area:
            return Cleared(changed)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return None
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < self.config.min_dart_area:
            return None

        raw = self._threshold(cv2.absdiff(gray, self.reference))
        tip, flight = self._find_tip(contour, raw, flight_direction)
        return Dart(tip=tip, contour=contour, axis=(tip, flight))

    def _find_tip(
        self, contour: np.ndarray, raw_mask: np.ndarray, flight_direction: Optional[FlightDirection]
    ) -> Tuple[Point, Point]:
        """Ends of the dart along its shaft axis, as (tip, flight)."""
        points = contour.reshape(-1, 2).astype(np.float64)
        vx, vy, x0, y0 = cv2.fitLine(points, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        direction = np.array([vx, vy])
        normal = np.array([-vy, vx])
        origin = np.array([x0, y0])

        along = (points - origin) @ direction
        lo, hi = along.min(), along.max()

        if self._flight_at_high_end(contour, raw_mask.shape, origin, direction, lo, hi, flight_direction):
            tip_t, flight_t = lo, hi
        else:
            tip_t, flight_t = hi, lo

        tip = self._trace_tip(raw_mask, origin, direction, normal, tip_t, flight_t)
        flight = origin + direction * flight_t
        return (float(tip[0]), float(tip[1])), (float(flight[0]), float(flight[1]))

    def _flight_at_high_end(
        self,
        contour: np.ndarray,
        shape: Tuple[int, ...],
        origin: np.ndarray,
        direction: np.ndarray,
        lo: float,
        hi: float,
        flight_direction: Optional[FlightDirection],
    ) -> bool:
        """Whether the flight is at the +direction end of the shaft axis."""
        if flight_direction is not None:
            middle = origin + direction * (lo + hi) / 2
            hint = flight_direction((float(middle[0]), float(middle[1])))
            if hint is not None:
                alignment = float(direction @ np.asarray(hint))
                if abs(alignment) >= self.config.min_direction_alignment:
                    return alignment > 0

        # No usable geometry: the flight end of the blob carries more area.
        filled = np.zeros(shape[:2], dtype=np.uint8)
        cv2.drawContours(filled, [contour], -1, 255, -1)
        ys, xs = np.nonzero(filled)
        t = (np.column_stack([xs, ys]) - origin) @ direction
        band = (hi - lo) * self.config.end_fraction
        return np.count_nonzero(t >= hi - band) >= np.count_nonzero(t <= lo + band)

    def _trace_tip(
        self,
        raw_mask: np.ndarray,
        origin: np.ndarray,
        direction: np.ndarray,
        normal: np.ndarray,
        tip_t: float,
        flight_t: float,
    ) -> np.ndarray:
        """Follow raw changed pixels past the cleaned blob's tip end to the steel point."""
        outward = 1.0 if tip_t > flight_t else -1.0
        start = tip_t * outward
        max_reach = abs(tip_t - flight_t) * self.config.tip_max_extension

        ys, xs = np.nonzero(raw_mask)
        offsets = np.column_stack([xs, ys]) - origin
        along = offsets @ direction * outward - start  # px beyond the blob's tip end
        across = offsets @ normal
        near = (np.abs(across) <= self.config.tip_lateral_px) & (along >= -1) & (along <= max_reach)
        along, across = along[near], across[near]

        reach = 0.0
        for step in np.unique(np.floor(along)):
            if step - reach > self.config.tip_max_gap_px:
                break
            reach = max(reach, step)

        # Centre the tip on the raw pixels at its end, which may sit off the fitted line.
        at_end = np.abs(along - reach) <= 1.5
        offset = float(np.median(across[at_end])) if at_end.any() else 0.0
        return origin + direction * (start + reach) * outward + normal * offset
