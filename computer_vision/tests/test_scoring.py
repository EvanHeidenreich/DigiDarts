import math

import numpy as np
import pytest

from computer_vision.src.calibration import CALIBRATION_LANDMARKS, BoardCalibration
from computer_vision.src.scoring import SEGMENT_ORDER, VIPER_SHOT_KING, Score, score_from_point


def polar(clockwise_deg, radius):
    rad = math.radians(clockwise_deg)
    return radius * math.sin(rad), radius * math.cos(rad)


def test_bulls():
    assert score_from_point(0, 0) == Score(25, 2)
    assert score_from_point(10, 0) == Score(25, 1)


@pytest.mark.parametrize("index,number", list(enumerate(SEGMENT_ORDER)))
def test_every_segment_and_ring(index, number):
    angle = index * 18
    assert score_from_point(*polar(angle, 60)) == Score(number, 1)
    assert score_from_point(*polar(angle, 103)) == Score(number, 3)
    assert score_from_point(*polar(angle, 130)) == Score(number, 1)
    assert score_from_point(*polar(angle, 166)) == Score(number, 2)
    assert score_from_point(*polar(angle, 180)) == Score(0, 0)


def test_segment_boundary_sides():
    # 20 spans -9..9 degrees, 1 is clockwise of it, 5 anticlockwise.
    assert score_from_point(*polar(8.9, 60)).segment == 20
    assert score_from_point(*polar(9.1, 60)).segment == 1
    assert score_from_point(*polar(-9.1, 60)).segment == 5


def test_labels():
    assert Score(20, 3).label == "T20"
    assert Score(25, 2).label == "BULL"
    assert Score(0, 0).value == 0


def test_calibration_round_trip(tmp_path):
    # Fake a camera looking at the board from an angle: an arbitrary homography.
    true_h = np.array([[0.9, 0.1, -400], [-0.05, -1.1, 300], [0.0002, 0.0001, 1.0]])
    true_cal = BoardCalibration(true_h)
    clicks = true_cal.board_to_pixel(np.array(list(CALIBRATION_LANDMARKS.values())))

    cal = BoardCalibration.from_landmark_clicks([tuple(p) for p in clicks])
    treble_20 = true_cal.board_to_pixel(np.array([polar(0, 103)]))[0]
    assert cal.score_pixel(*treble_20) == Score(20, 3)

    path = tmp_path / "cal.json"
    cal.save(path)
    np.testing.assert_allclose(BoardCalibration.load(path).homography, cal.homography)


def test_landmarks_sit_on_double_ring():
    for x, y in CALIBRATION_LANDMARKS.values():
        assert math.hypot(x, y) == pytest.approx(VIPER_SHOT_KING.double_outer_radius)
