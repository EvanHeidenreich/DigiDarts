# https://docs.opencv.org/5.0/tutorials/others/optical_flow.html
# ^ Reference

import cv2
import numpy 

cap = cv2.VideoCapture(0)

ret, firstFrame = cap.read()
prvs = cv2.cvtColor(firstFrame, cv2.COLOR_BGR2GRAY)
hsv = numpy.zeros_like(firstFrame)  # Hue, Saturation, Value
hsv[..., 1] = 255

while True:
    ret, currentFrame = cap.read()
    # frame = cv2.resize(frame, (640, 480))
    if not ret:
        print('No frames received')
        break

    next = cv2.cvtColor(currentFrame, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(prvs, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang * 180 / numpy.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    cv2.imshow('Bro', bgr)

    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break
    elif k == ord('s'):
        cv2.imwrite('opticalfb.png', currentFrame)
        cv2.imwrite('opticalhsv.png', bgr)

    prvs = next

    # frame = cv2.resize(frame, (1080, 720))
    # data = cv2.imencode('.jpg', frame)[1].tobytes()
    # try:
    #     nparr = numpy.fromstring(data, numpy.uint8)
    #     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #     cv2.imshow('Client', img)
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    # except:
    #     break

cap.release()
cv2.destroyAllWindows()