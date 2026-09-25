# Computer Vision

Capture → detect → calibrate → score pipeline for tracking dart throws.

## Structure

```
computer_vision/
├── src/
│   ├── main.py          # CLI entry point — opens a camera and runs the loop
│   ├── pipeline.py       # DartsVisionPipeline: wires the pieces below together
│   ├── capture.py        # CameraStream: cv2.VideoCapture wrapper
│   ├── detection.py       # detect_dart_tip(): finds the tip in a frame
│   ├── calibration.py     # BoardCalibration: pixel -> board-space mm
│   └── scoring.py          # score_from_point(): board-space mm -> Score
├── tests/
│   └── test_scoring.py
└── experiments/           # scratch space / notebooks, not part of the package
```

## What's real vs. a placeholder

- **`scoring.py`** is fully implemented — it's pure geometry (standard
  dartboard ring radii + 20 segment angles), so it doesn't need a camera
  or model to work or to be tested.
- **`detection.py`** currently finds the dart tip with simple frame
  differencing against a reference "empty board" frame. This is a stand-in
  for the custom-trained model described in the top-level
  [README](../README.md) — swap the body of `detect_dart_tip()` for a
  model call once that exists; the `Detection` return type can stay the
  same so `pipeline.py` doesn't need to change.
- **`calibration.py`** defaults to an identity mapping (pixels treated as
  mm). Once the camera rig is mounted, replace that with
  `BoardCalibration.from_point_correspondences(...)` using real
  measured landmarks on the board, and save it with `.save()` so
  `main.py --calibration` can load it.

## Running it locally

```bash
pip install -r computer_vision/requirements.txt
python -m computer_vision.src.main --camera 0
```

Point a webcam at anything, then move something into frame — it'll be
scored as if it were a dart tip landing at that pixel location, useful for
sanity-checking the pipeline before real hardware is wired up.

## Tests

```bash
pip install -r computer_vision/requirements.txt
python -m pytest computer_vision/tests
```

## Note on OpenCV package

This uses `opencv-python` (with GUI support) rather than the
`opencv-python-headless` build the backend's Docker image uses, since
local CV development benefits from being able to `cv2.imshow()` a frame.
The backend container has no display, hence headless there.
