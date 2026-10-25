import cv2
import numpy 

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    # frame = cv2.resize(frame, (640, 480))
    frame = cv2.resize(frame, (1080, 720))
    data = cv2.imencode('.jpg', frame)[1].tobytes()
    try:
        nparr = numpy.fromstring(data, numpy.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imshow('Window', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except:
        break

cap.release()
cv2.destroyAllWindows()