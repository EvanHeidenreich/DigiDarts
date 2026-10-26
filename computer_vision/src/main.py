# Live dart scoring: camera -> detector -> calibration -> score, with the board
# overlay drawn on the feed.
#
# Run from the repo root:
#   python -m computer_vision.src.main --camera 0 --calibration calibration.json
#
# It asks the camera for 1920x1200 (--width / --height) and prints what it got.
# The Arducam only offers 960x600 at 10 fps over a USB 2 link, so use a USB 3
# cable and port for full resolution.
#
# If the calibration file doesn't exist, click the four landmarks shown at the
# top of the window (where a radial wire meets the OUTSIDE of the double ring),
# the same as experiments/board_calibration.py.
#
# Keys: q / Esc = quit, r = reset reference + clear darts, c = recalibrate,
#       s = save calibration, m = toggle the detector mask window,
#       f = flip the last dart's tip and flight ends if it picked the wrong one

import argparse
import sys
from pathlib import Path

# Allow running this file directly (e.g. VS Code's Run button), not just with -m
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cv2

from computer_vision.src.calibration import CALIBRATION_LANDMARKS, BoardCalibration
from computer_vision.src.detector import Cleared, Dart, DartDetector, DetectorConfig, State
from computer_vision.src.overlay import draw_board_overlay

TIP_COLOR = (0, 0, 255)
AXIS_COLOR = (255, 0, 255)
TEXT_COLOR = (0, 255, 0)

parser = argparse.ArgumentParser()
parser.add_argument("--camera", type=int, default=0)
parser.add_argument("--calibration", default="calibration.json", help="file to load from and save to with 's'")
parser.add_argument("--width", type=int, default=1920, help="requested camera resolution; the camera may pick another")
parser.add_argument("--height", type=int, default=1200)
args = parser.parse_args()

cap = cv2.VideoCapture(args.camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
ret, frame = cap.read()
if not ret:
    sys.exit("No frames received")
image_size = (frame.shape[1], frame.shape[0])
print(f"Camera {args.camera}: {image_size[0]}x{image_size[1]} at {cap.get(cv2.CAP_PROP_FPS):.0f} fps")

landmark_names = list(CALIBRATION_LANDMARKS)
clicks = []
mouse = (0, 0)
calibration = BoardCalibration.load(args.calibration).resized(image_size) if Path(args.calibration).exists() else None
detector = DartDetector(DetectorConfig.for_resolution(*image_size))
darts = []  # (Dart, Score) for the current turn
show_mask = False


def on_mouse(event, x, y, flags, param):
    global mouse, calibration
    mouse = (x, y)
    if event == cv2.EVENT_LBUTTONDOWN and calibration is None:
        clicks.append((x, y))
        if len(clicks) == len(landmark_names):
            calibration = BoardCalibration.from_landmark_clicks(clicks).resized(image_size)
            detector.reset()


def draw_darts(frame):
    for i, (dart, score) in enumerate(darts, start=1):
        tip = tuple(int(c) for c in dart.tip)
        flight = tuple(int(c) for c in dart.axis[1])
        cv2.drawContours(frame, [dart.contour], -1, AXIS_COLOR, 1)
        cv2.line(frame, tip, flight, AXIS_COLOR, 1, cv2.LINE_AA)
        cv2.circle(frame, tip, 5, TIP_COLOR, -1)
        cv2.putText(frame, f"{i}: {score.label}", (tip[0] + 8, tip[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, TIP_COLOR, 2)

    labels = "  ".join(score.label for _, score in darts) or "-"
    total = sum(score.value for _, score in darts)
    cv2.putText(frame, f"Darts: {labels}   Total: {total}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, TEXT_COLOR, 2)
    state_color = (0, 165, 255) if detector.state == State.MOTION else TEXT_COLOR
    cv2.putText(frame, f"Detector: {detector.state.value}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2)


# Resizable, since full resolution can be larger than the screen. Mouse
# positions still come back in frame pixels.
cv2.namedWindow("DigiDarts", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.setMouseCallback("DigiDarts", on_mouse)

while True:
    ret, frame = cap.read()
    if not ret:
        print("No frames received")
        break

    if calibration is None:
        for point in clicks:
            cv2.circle(frame, point, 4, (0, 0, 255), -1)
        prompt = f"Click the {landmark_names[len(clicks)]} wire on the outer double ring"
        cv2.putText(frame, prompt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    else:
        event = detector.update(frame, lambda p: calibration.out_of_board_direction(*p, image_size))
        if isinstance(event, Dart):
            score = calibration.score_pixel(*event.tip)
            darts.append((event, score))
            print(f"Dart {len(darts)}: {score.label} ({score.value}) at pixel {event.tip}")
        elif isinstance(event, Cleared):
            if darts:
                print(f"Board cleared, turn total {sum(s.value for _, s in darts)}")
            darts.clear()

        frame = draw_board_overlay(frame, calibration)
        draw_darts(frame)
        hover = calibration.score_pixel(*mouse).label
        cv2.putText(frame, hover, (mouse[0] + 12, mouse[1] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

    cv2.imshow("DigiDarts", frame)
    if show_mask and detector.last_mask is not None:
        cv2.imshow("Detector mask", detector.last_mask)

    k = cv2.waitKey(1) & 0xFF
    if k in (27, ord("q")):
        break
    elif k == ord("r"):
        detector.reset()
        darts.clear()
    elif k == ord("c"):
        clicks.clear()
        calibration = None
        darts.clear()
    elif k == ord("s") and calibration is not None:
        calibration.save(args.calibration)
        print(f"Saved calibration to {args.calibration}")
    elif k == ord("f") and darts and calibration is not None:
        dart, _ = darts[-1]
        flipped = Dart(tip=dart.axis[1], contour=dart.contour, axis=(dart.axis[1], dart.axis[0]))
        darts[-1] = (flipped, calibration.score_pixel(*flipped.tip))
        print(f"Dart {len(darts)} flipped: {darts[-1][1].label} ({darts[-1][1].value})")
    elif k == ord("m"):
        show_mask = not show_mask
        if not show_mask and detector.last_mask is not None:
            cv2.destroyWindow("Detector mask")

cap.release()
cv2.destroyAllWindows()
