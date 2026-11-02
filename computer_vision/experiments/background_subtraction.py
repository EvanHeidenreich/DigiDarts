# Reference: https://docs.opencv.org/5.0/tutorials/others/background_subtraction.html

# Denoising Reference: https://docs.opencv.org/5.0/py_tutorials/py_photo/py_non_local_means/py_non_local_means.html

import argparse
import os
import cv2
import numpy 

parser = argparse.ArgumentParser()
parser.add_argument('--algo', type=str, help='Background subtraction method (MOG2, KNN).', default='MOG2')
args = parser.parse_args()

# create Background Subtractor objects
if args.algo == 'MOG2':
    backSub = cv2.createBackgroundSubtractorMOG2()
else:
    backSub = cv2.createBackgroundSubtractorKNN()


framesToCapture = 0
# frameDirectory = f"bro"
# frameDirectory = f"bro"
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
frameDirectory = os.path.join(scriptDirectory, "data/")
os.makedirs(frameDirectory, exist_ok=True)


placeholderI = 0

cap = cv2.VideoCapture(0)

print(frameDirectory)

while True:
    ret, frame = cap.read()
    frame = cv2.resize(frame, (1080, 720))

    # update the background model
    fgMask = backSub.apply(frame)

    cv2.imshow('Frame', frame)
    cv2.imshow('FG Mask', fgMask)

    key = cv2.waitKey(1) & 0xFF

    ## if cv2.waitKey(1) & 0xFF == ord('q'):
    if key == ord('q'):
        break
    if key == ord('p'):
        # cv2.destroyWindow('Denoised')
        # cv2.imwrite()
        # img = cv2.imread(frame.imag)
        # dst = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        # cv2.imshow('Denoised', dst)
        # framesToCapture = 5
        placeholderI = placeholderI + 1

        frameDupe = frame
        alphaMask = backSub.apply(frameDupe)

        _, alpha = cv2.threshold(alphaMask, 100, 255, cv2.THRESH_BINARY) # 2nd parameter was 200, trying 50
        bgra = cv2.cvtColor(frameDupe, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = alpha # moving pixels opaque, background transparent

        maskStatus = cv2.imwrite(f"{frameDirectory}Mask_{placeholderI}.png", alphaMask)
        operationStatus = cv2.imwrite(f"{frameDirectory}FrameWithMask_{placeholderI}.png", bgra)

        # print("The mask was made into a .png file: {maskStatus}\nThe frame with the mask was made into a .png file: {operationStatus}")
        print(maskStatus, f"{frameDirectory}Mask_{placeholderI}.png")
        print("\n" + str(bgra.shape) + "\n")
        print(operationStatus, f"{frameDirectory}FrameWithMask_{placeholderI}.png")

        print("\n" + str(numpy.unique(alphaMask)) + "\n")
        print("\n" + str(numpy.unique(alpha)) + "\n")
        print("\n" + str(numpy.count_nonzero(alpha)) + "\n")
        
        # THIS CODE ASSUMES THAT alphaMask IS IN COLOR 
        # NOT IN GRAYSCALE
        #  
        # gray = cv2.cvtColor(alphaMask, cv2.COLOR_BGR2GRAY)

        # threshold = 10
        # alpha = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

        # b, g, r = cv2.split(alphaMask)
        # bgra = cv2.merge([b, g, r, alpha])

        # cv2.imwrite(f"{frameDirectory}Mask_{placeholderI}.png", alphaMask)


        # result = numpy.zeros_like(frameDupe)
        # frameDupe.copyTo(result, alphaMask)

        # result = cv2.bitwise_and(frameDupe, frameDupe, mask=fgMask)

        # cv2.imwrite(f"{frameDirectory}FrameWithMask_{placeholderI}.png", result)

        # Alpha = 0 where the pixel is black or close to black depending on threshold.

        # img = cv2.imwrite(f"{frameDirectory}/FrameWithMask_{placeholderI}.png", frame)


    # if framesToCapture > 0:
    #    cv2.imwrite(f"{frameDirectory}/frame_{framesToCapture}.jpg", frame)
    #    cv2.imwrite(f"{frameDirectory}/mask_{framesToCapture}.jpg", fgMask)
        

    # if key == ord('b'):
        # img = [cv2.imreadmulti]

cap.release()
cv2.destroyAllWindows()