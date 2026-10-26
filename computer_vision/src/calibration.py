"""Mapping between camera pixels and Viper Shot King board space (mm).
    The dart board is a plannar surface, with dimensions of 17.75"W x 17.75"H.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np

from .scoring import SEGMENT_ANGLE_DEG, VIPER_SHOT_KING, Score, score_from_point

Point = Tuple[float, float]

# How far off the board to look when projecting "out of the board" directions.
# Roughly a dart's length; only the resulting direction is used.
DART_LENGTH_MM = 50.0
# Below this ratio of out-of-board to in-plane image movement, the camera is too
# close to head-on for the out-of-board direction to be trusted.
MIN_OUT_OF_BOARD_RATIO = 0.25


def _board_point(clockwise_deg: float, radius_mm: float) -> Point:
    rad = math.radians(clockwise_deg)
    return (radius_mm * math.sin(rad), radius_mm * math.cos(rad))


# Where the radial wire between two numbers meets the outside of the double
# ring. These corners are sharp on a bristle board, so they're easy to click
# accurately, and four of them spread around the board pin down a homography.
CALIBRATION_LANDMARKS = {
    "20/1": _board_point(SEGMENT_ANGLE_DEG / 2, VIPER_SHOT_KING.double_outer_radius),
    "6/10": _board_point(90 + SEGMENT_ANGLE_DEG / 2, VIPER_SHOT_KING.double_outer_radius),
    "3/19": _board_point(180 + SEGMENT_ANGLE_DEG / 2, VIPER_SHOT_KING.double_outer_radius),
    "11/14": _board_point(270 + SEGMENT_ANGLE_DEG / 2, VIPER_SHOT_KING.double_outer_radius),
}


def _estimate_focal_length(g1: np.ndarray, g2: np.ndarray, image_extent: int) -> float:
    """Focal length (px) making the homography's rotation columns orthonormal.

    Falls back to the image size, a typical webcam field of view, when the view
    is too square-on for the estimate to be well conditioned.
    """
    candidates = []
    if abs(g1[2] * g2[2]) > 1e-12:  # r1 . r2 = 0
        candidates.append(-(g1[0] * g2[0] + g1[1] * g2[1]) / (g1[2] * g2[2]))
    if abs(g1[2] ** 2 - g2[2] ** 2) > 1e-12:  # |r1| = |r2|
        candidates.append((g2[0] ** 2 + g2[1] ** 2 - g1[0] ** 2 - g1[1] ** 2) / (g1[2] ** 2 - g2[2] ** 2))
    for f_squared in candidates:
        if f_squared > 0:
            return float(np.clip(math.sqrt(f_squared), 0.3 * image_extent, 4.0 * image_extent))
    return float(image_extent)


@dataclass
class BoardCalibration:
    # 3x3 homography taking (u, v, 1) pixels to (x, y, w) board-space mm.
    homography: np.ndarray
    # (width, height) of the camera frames the pixels refer to, if known.
    image_size: Optional[Tuple[int, int]] = None

    @classmethod
    def identity(cls) -> "BoardCalibration":
        return cls(np.eye(3))

    @classmethod
    def from_point_correspondences(
        cls, pixel_points: Sequence[Point], board_points: Sequence[Point]
    ) -> "BoardCalibration":
        if len(pixel_points) != len(board_points) or len(pixel_points) < 4:
            raise ValueError("need at least 4 matching pixel/board points")
        src = np.asarray(pixel_points, dtype=np.float64)
        dst = np.asarray(board_points, dtype=np.float64)
        homography, _ = cv2.findHomography(src, dst)
        if homography is None:
            raise ValueError("points are degenerate (collinear or duplicated)")
        return cls(homography)

    @classmethod
    def from_landmark_clicks(cls, pixel_points: Sequence[Point]) -> "BoardCalibration":
        """Pixels clicked in CALIBRATION_LANDMARKS order."""
        return cls.from_point_correspondences(pixel_points, list(CALIBRATION_LANDMARKS.values()))

    def pixel_to_board(self, u: float, v: float) -> Point:
        x, y = cv2.perspectiveTransform(np.array([[[u, v]]], dtype=np.float64), self.homography)[0, 0]
        return float(x), float(y)

    def board_to_pixel(self, points_mm: np.ndarray) -> np.ndarray:
        """(N, 2) board-space mm -> (N, 2) pixels."""
        pts = np.asarray(points_mm, dtype=np.float64).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(pts, np.linalg.inv(self.homography)).reshape(-1, 2)

    def score_pixel(self, u: float, v: float) -> Score:
        return score_from_point(*self.pixel_to_board(u, v))

    def out_of_board_direction(self, u: float, v: float, image_size: Tuple[int, int]) -> Optional[Point]:
        """Unit image direction that something sticking out of the board at (u, v) points.

        A dart's flight sits off the board toward the camera, so this points from
        its tip toward its flight. The camera pose is recovered from the homography,
        assuming square pixels and the principal point at the image centre. Returns
        None when the camera faces the board too squarely for this to be reliable.
        """
        width, height = image_size
        center = np.array([[1.0, 0.0, width / 2], [0.0, 1.0, height / 2], [0.0, 0.0, 1.0]])
        # Board mm -> centred pixels, which is K [r1 r2 t] up to scale.
        g = np.linalg.inv(center) @ np.linalg.inv(self.homography)
        f = _estimate_focal_length(g[:, 0], g[:, 1], max(width, height))

        r1, r2, t = (g[:, i] * np.array([1 / f, 1 / f, 1.0]) for i in range(3))
        scale = 1.0 / np.linalg.norm(r1)
        if t[2] < 0:  # the board must be in front of the camera
            scale = -scale
        r1, r2, t = r1 * scale, r2 * scale, t * scale
        r3 = np.cross(r1, r2)
        r3 /= np.linalg.norm(r3)
        # The camera centre is at -R^T t in board space; its z says which side of the board it's on.
        toward_camera = 1.0 if -(r3 @ t) > 0 else -1.0

        def project(p: np.ndarray) -> np.ndarray:
            return f * p[:2] / p[2]

        x, y = self.pixel_to_board(u, v)
        base = x * r1 + y * r2 + t
        out = project(base + toward_camera * DART_LENGTH_MM * r3) - project(base)
        sideways = project(base + DART_LENGTH_MM * r1) - project(base)
        if np.linalg.norm(out) < MIN_OUT_OF_BOARD_RATIO * np.linalg.norm(sideways):
            return None
        out /= np.linalg.norm(out)
        return float(out[0]), float(out[1])

    def resized(self, image_size: Tuple[int, int]) -> "BoardCalibration":
        """The same calibration for frames of a different resolution from the same camera."""
        if self.image_size is None or tuple(self.image_size) == tuple(image_size):
            return BoardCalibration(self.homography, tuple(image_size))
        sx = image_size[0] / self.image_size[0]
        sy = image_size[1] / self.image_size[1]
        return BoardCalibration(self.homography @ np.diag([1 / sx, 1 / sy, 1.0]), tuple(image_size))

    def save(self, path: str | Path) -> None:
        data = {"homography": self.homography.tolist()}
        if self.image_size is not None:
            data["image_size"] = list(self.image_size)
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "BoardCalibration":
        data = json.loads(Path(path).read_text())
        image_size = tuple(data["image_size"]) if "image_size" in data else None
        return cls(np.array(data["homography"], dtype=np.float64), image_size)
