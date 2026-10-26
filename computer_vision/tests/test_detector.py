import math

import cv2
import numpy as np
import pytest

from computer_vision.src.calibration import BoardCalibration
from computer_vision.src.detector import Dart, DartDetector

SIZE = (640, 480)


def draw_dart(frame, tip, angle_deg, flight_shape="kite", point=True):
    """Steel point, barrel, shaft, then a flight at the back, all pointing away from tip at angle_deg."""
    d = np.array([math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))])
    n = np.array([-d[1], d[0]])
    tip = np.asarray(tip, dtype=float)

    def at(t, s=0.0):
        p = tip + d * t + n * s
        return int(round(p[0])), int(round(p[1]))

    if point:
        cv2.line(frame, at(0), at(25), 255, 2)  # thin steel point
    cv2.line(frame, at(25), at(70), 255, 9 if point else 12)  # barrel
    cv2.line(frame, at(70), at(100), 255, 4)  # shaft
    if flight_shape == "kite":
        flight = [at(95), at(125, 22), at(160), at(125, -22)]
    elif flight_shape == "edge":
        # Seen nearly edge-on, the flight is thinner than the barrel.
        flight = [at(95, -3), at(150, -6), at(158, -2), at(158, 2), at(150, 6), at(95, 3)]
    else:
        flight = [at(95, -5), at(155, -24), at(155, 24), at(95, 5)]
    cv2.fillPoly(frame, [np.array(flight, dtype=np.int32)], 255)


def throw(detector, tip, angle_deg, flight_shape="kite", flight_direction=None, point=True):
    board = np.full(SIZE[::-1], 60, dtype=np.uint8)
    for _ in range(3):
        detector.update(board)
    with_dart = board.copy()
    draw_dart(with_dart, tip, angle_deg, flight_shape, point)
    event = None
    detector.update(with_dart)  # the arrival registers as motion
    for _ in range(detector.config.settle_frames):
        event = detector.update(with_dart, flight_direction) or event
    return event


@pytest.mark.parametrize("angle", [0, 37, 90, 160, 225, 300])
@pytest.mark.parametrize("flight_shape", ["kite", "fan"])
def test_tip_found_at_steel_point_without_geometry(angle, flight_shape):
    tip = (320, 240)
    event = throw(DartDetector(), tip, angle, flight_shape)
    assert isinstance(event, Dart)
    assert math.dist(event.tip, tip) < 4


@pytest.mark.parametrize("angle", [0, 120, 250])
def test_flight_direction_decides_the_ends(angle):
    tip = (320, 240)
    d = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    event = throw(DartDetector(), tip, angle, flight_direction=lambda p: d)
    assert math.dist(event.tip, tip) < 4

    # A hint pointing the other way wins over the area heuristic.
    backwards = throw(DartDetector(), tip, angle, flight_direction=lambda p: (-d[0], -d[1]))
    assert math.dist(backwards.tip, tip) > 100


@pytest.mark.parametrize("angle", [0, 120, 250])
def test_flight_direction_handles_hidden_point_and_edge_on_flight(angle):
    # The shape alone points the wrong way here: the barrel end is the bulkier one.
    tip = (320, 240)
    d = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    event = throw(DartDetector(), tip, angle, "edge", flight_direction=lambda p: d, point=False)
    barrel_front = (tip[0] + 25 * d[0], tip[1] + 25 * d[1])
    assert math.dist(event.tip, barrel_front) < 10  # the barrel's rounded, blurred end reaches a few px past it


def camera_calibration(rvec, tvec, f=800.0):
    k = np.array([[f, 0, SIZE[0] / 2], [0, f, SIZE[1] / 2], [0, 0, 1]])
    r, _ = cv2.Rodrigues(np.asarray(rvec, dtype=float))
    board_to_pixel = k @ np.column_stack([r[:, 0], r[:, 1], tvec])
    return BoardCalibration(np.linalg.inv(board_to_pixel)), k, r, np.asarray(tvec, dtype=float)


@pytest.mark.parametrize("rvec", [(2.6, 0.0, 0.0), (0.0, 2.7, 0.3), (2.5, 0.4, 0.2)])
def test_out_of_board_direction_matches_the_camera(rvec):
    calibration, k, r, t = camera_calibration(rvec, (10.0, -20.0, 600.0))
    board_point = np.array([30.0, 40.0, 0.0])
    camera_z = -(r[:, 2] @ t)
    lifted = board_point + np.array([0, 0, 50.0 * np.sign(camera_z)])

    def project(p):
        q = k @ (r @ p + t)
        return q[:2] / q[2]

    expected = project(lifted) - project(board_point)
    expected /= np.linalg.norm(expected)
    u, v = project(board_point)
    got = calibration.out_of_board_direction(u, v, SIZE)
    assert got is not None
    assert np.dot(got, expected) > math.cos(math.radians(5))


def test_out_of_board_direction_is_none_head_on():
    calibration, _, _, _ = camera_calibration((math.pi, 0.0, 0.0), (0.0, 0.0, 600.0))
    assert calibration.out_of_board_direction(320, 240, SIZE) is None


def test_calibration_resized_scores_the_same_spot():
    calibration, k, r, t = camera_calibration((2.6, 0.0, 0.0), (10.0, -20.0, 600.0))
    calibration.image_size = SIZE
    doubled = calibration.resized((SIZE[0] * 2, SIZE[1] * 2))
    for u, v in [(320, 240), (100, 400), (500, 80)]:
        assert np.allclose(calibration.pixel_to_board(u, v), doubled.pixel_to_board(2 * u, 2 * v))


def test_calibration_round_trips_image_size(tmp_path):
    calibration = BoardCalibration(np.eye(3), (960, 600))
    calibration.save(tmp_path / "c.json")
    assert BoardCalibration.load(tmp_path / "c.json").image_size == (960, 600)


def test_detector_config_scales_with_resolution():
    from computer_vision.src.detector import DetectorConfig

    assert DetectorConfig.for_resolution(960, 600) == DetectorConfig()
    big = DetectorConfig.for_resolution(1920, 1200)
    assert big.min_dart_area == 4 * DetectorConfig().min_dart_area
    assert big.blur_kernel % 2 == 1
