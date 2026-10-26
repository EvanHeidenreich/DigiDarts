# DigiDarts — Computer Vision Dart Detector

A single camera watches a Viper Shot King bristle dartboard. When a dart lands,
the program finds its tip, maps that pixel onto the board, and reports the score
(e.g. `T20`, `D16`, `BULL`). Everything is classical OpenCV (no trained model).

## How it works

```
camera frame ──► detector.py ──► calibration.py ──► scoring.py ──► score
                 (find the tip)   (pixel → board mm)  (mm → T20 etc.)
```

1. **Calibration** ([src/calibration.py](src/calibration.py)): On startup the
   user clicks four landmarks: the points where the 20/1, 6/10, 3/19 and 11/14
   wires meet the outside of the double ring. Their real positions in
   millimetres are known, so OpenCV computes a **homography**, a 3×3 matrix that
   maps any camera pixel onto the flat board, even when the camera views it at an
   angle. The calibration is saved to `calibration.json` for reuse.

2. **Detection** ([src/detector.py](src/detector.py)): Uses frame differencing
   with a small state machine:
   - **Idle**: the board is still. Keep a blurred grayscale *reference* frame
     of it, updating slowly so gradual lighting changes are absorbed.
   - **Motion**: many pixels changed between frames, so a dart is arriving.
     Wait until the image has been still for a few frames.
   - **Analyse**: diff the settled frame against the reference, threshold it,
     clean it with morphology, and take the largest blob as the new dart. The
     settled frame becomes the new reference, so each dart is isolated from
     the ones already in the board.
   - **Finding the tip**: fit a line through the blob (the shaft axis). To
     decide which end is the tip, use the camera pose recovered from the
     homography (the flight sticks out *toward* the camera). If the camera
     faces the board too squarely to tell, assume the end with more area is
     the flight. Cleanup erodes the thin steel point, so the tip is then
     traced outward along the shaft through the raw difference pixels.
   - **Cleared**: if the board looks empty again, or a change far larger than
     a dart appears (a hand pulling darts), the turn is reset.

3. **Scoring** ([src/scoring.py](src/scoring.py)): Pure geometry. The tip's
   board position is converted to polar coordinates. The **radius** picks the
   ring (bull, single, treble, double, miss) using regulation WDF dimensions,
   and the **angle** picks one of the 20 numbered segments.

4. **Overlay** ([src/overlay.py](src/overlay.py)): Projects the board's rings,
   wires and numbers back onto the live video, so you can check the calibration
   by eye. Detected darts are drawn with their tip, axis and score.

## Running it

```bash
pip install -r computer_vision/requirements.txt
python -m computer_vision.src.main --camera 0
```

Keys: `q` quit · `r` reset · `c` recalibrate · `s` save calibration ·
`m` show the detector mask · `f` flip tip/flight on the last dart if it guessed wrong.

## Tests

```bash
python -m pytest computer_vision/tests
```

[tests/test_scoring.py](tests/test_scoring.py) checks the board geometry, and
[tests/test_detector.py](tests/test_detector.py) runs the detector on
synthetic frames.

## Layout

```
computer_vision/
├── src/           main program (main.py is the entry point)
├── tests/         unit tests
└── experiments/   standalone prototypes (optical flow, calibration clicker)
```
