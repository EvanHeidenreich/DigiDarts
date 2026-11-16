# Reference: https://docs.opencv.org/5.0/main_modules/imgproc_motion.html
# Reference: https://docs.opencv.org/5.x/d1/dc5/tutorial_background_subtraction.html

# DISCLAIMER: Wrote using the assistance of Claude

import os
import numpy
import cv2

FRAME_SIZE = (1080, 720)   # (width, height) for cv2.resize
N = 5                     # number of frames to capture per button press
VOTE_THRESHOLD = 0.5       # fraction of frames a pixel must be foreground in

scriptDirectory = os.path.dirname(os.path.abspath(__file__))
frameDirectory = os.path.join(scriptDirectory, "data", "burst")
os.makedirs(frameDirectory, exist_ok=True)

placeholderI = 0
kernel = numpy.ones((5, 5), numpy.uint8)

# detectShadows=False keeps the mask strictly 0/255
backSub = cv2.createBackgroundSubtractorMOG2(detectShadows=False)

cap = cv2.VideoCapture(0)

print(frameDirectory)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read from camera")
        break
    frame = cv2.resize(frame, FRAME_SIZE)

    # update the background model
    fgMask = backSub.apply(frame)

    cv2.imshow('Frame', frame)
    cv2.imshow('FG Mask', fgMask)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    if key == ord('p'):
        placeholderI += 1

        # fresh accumulators for every burst
        votes = numpy.zeros(fgMask.shape, float)    # per-pixel foreground count
        colorAcc = numpy.zeros(frame.shape, float)  # sum of color frames
        got = 0

        for _ in range(N):
            ret, f = cap.read()
            if not ret:
                continue
            f = cv2.resize(f, FRAME_SIZE)

            # learningRate=0 freezes the model so the change isn't absorbed
            m = backSub.apply(f, learningRate=0)

            votes += (m == 255)
            cv2.accumulate(f, colorAcc)
            got += 1

            cv2.waitKey(30)  # give the camera time to deliver a new frame

        if got == 0:
            print("No frames captured")
            continue

        weight = votes / got                       # 0..1 per pixel
        avg = (colorAcc / got).astype(numpy.uint8) # noise-reduced color image

        mask = (weight >= VOTE_THRESHOLD).astype(numpy.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # keep only the region with the largest change
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            print("No changed region found")
            continue

        biggest = max(cnts, key=cv2.contourArea)
        largest = numpy.zeros_like(mask)
        cv2.drawContours(largest, [biggest], -1, 255, cv2.FILLED)

        bgra = cv2.cvtColor(avg, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = largest  # changed region opaque, everything else transparent

        maskPath = os.path.join(frameDirectory, f"Mask_{placeholderI}.png")
        framePath = os.path.join(frameDirectory, f"FrameWithMask_{placeholderI}.png")

        maskStatus = cv2.imwrite(maskPath, largest)
        operationStatus = cv2.imwrite(framePath, bgra)

        print(maskStatus, maskPath)
        print(operationStatus, framePath)
        print(f"frames used: {got}, bgra shape: {bgra.shape}")

cap.release()
cv2.destroyAllWindows()