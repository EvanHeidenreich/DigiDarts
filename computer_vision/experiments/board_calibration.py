# Interactive calibration for the Viper Shot King.
#
# Run from the repo root:
#   python -m computer_vision.experiments.board_calibration --camera 0
#
# Click the four landmarks in the order shown at the top of the window (each is
# where a radial wire meets the OUTSIDE of the double ring). Once all four are
# in, the board layout is drawn over the feed and hovering the mouse shows the
# score at that spot, so you can check the fit.
#
# Keys: r = reset clicks, s = save calibration, q / Esc = quit

import argparse
import sys
from pathlib import Path

# Allow running this file directly (e.g. VS Code's Run button), not just with -m
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cv2

from computer_vision.src.calibration import CALIBRATION_LANDMARKS, BoardCalibration
from computer_vision.src.overlay import draw_board_overlay

parser = argparse.ArgumentParser()
parser.add_argument("--camera", type=int, default=0)
parser.add_argument("--output", default="calibration.json", help="where 's' saves the calibration")
parser.add_argument("--load", help="start from an existing calibration file")
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
calibration = BoardCalibration.load(args.load).resized(image_size) if args.load else None


def on_mouse(event, x, y, flags, param):
    global mouse, calibration
    mouse = (x, y)
    if event == cv2.EVENT_LBUTTONDOWN and calibration is None:
        clicks.append((x, y))
        if len(clicks) == len(landmark_names):
            calibration = BoardCalibration.from_landmark_clicks(clicks).resized(image_size)


cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.setMouseCallback("Calibration", on_mouse)

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
        frame = draw_board_overlay(frame, calibration)
        label = calibration.score_pixel(*mouse).label
        cv2.putText(frame, label, (mouse[0] + 12, mouse[1] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Calibration", frame)

    k = cv2.waitKey(1) & 0xFF
    if k in (27, ord("q")):
        break
    elif k == ord("r"):
        clicks.clear()
        calibration = None
    elif k == ord("s") and calibration is not None:
        calibration.save(args.output)
        print(f"Saved calibration to {args.output}")

cap.release()
cv2.destroyAllWindows()
