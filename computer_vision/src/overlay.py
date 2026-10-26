"""Draw the Viper Shot King layout on top of a camera frame."""

from __future__ import annotations

import math

import cv2
import numpy as np

from .calibration import BoardCalibration
from .scoring import SEGMENT_ANGLE_DEG, SEGMENT_ORDER, VIPER_SHOT_KING, BoardSpec

WIRE_COLOR = (0, 255, 255)
NUMBER_COLOR = (255, 255, 255)


def _circle(radius_mm: float, samples: int = 180) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, samples, endpoint=False)
    return np.stack([radius_mm * np.cos(t), radius_mm * np.sin(t)], axis=1)


def draw_board_overlay(
    frame: np.ndarray, calibration: BoardCalibration, spec: BoardSpec = VIPER_SHOT_KING
) -> np.ndarray:
    """Returns a copy of `frame` with rings, segment wires and numbers drawn on."""
    out = frame.copy()

    # Circles in board space become ellipses in the image, so sample and project.
    for radius in (
        spec.inner_bull_radius,
        spec.outer_bull_radius,
        spec.treble_inner_radius,
        spec.treble_outer_radius,
        spec.double_inner_radius,
        spec.double_outer_radius,
    ):
        pixels = calibration.board_to_pixel(_circle(radius)).astype(np.int32)
        cv2.polylines(out, [pixels], isClosed=True, color=WIRE_COLOR, thickness=1, lineType=cv2.LINE_AA)

    for i, number in enumerate(SEGMENT_ORDER):
        boundary = math.radians(i * SEGMENT_ANGLE_DEG - SEGMENT_ANGLE_DEG / 2)
        direction = np.array([math.sin(boundary), math.cos(boundary)])
        wire = calibration.board_to_pixel(
            np.array([direction * spec.outer_bull_radius, direction * spec.double_outer_radius])
        ).astype(int)
        cv2.line(out, tuple(wire[0]), tuple(wire[1]), WIRE_COLOR, 1, cv2.LINE_AA)

        middle = math.radians(i * SEGMENT_ANGLE_DEG)
        label_radius = (spec.double_outer_radius + spec.board_radius) / 2
        u, v = calibration.board_to_pixel(
            np.array([[label_radius * math.sin(middle), label_radius * math.cos(middle)]])
        )[0].astype(int)
        text = str(number)
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.putText(out, text, (u - w // 2, v + h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, NUMBER_COLOR, 1, cv2.LINE_AA)

    return out
