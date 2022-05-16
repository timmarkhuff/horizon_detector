import cv2
import numpy as np

path = "C:/Users/Owner/Desktop/runway_detector (in progress)/produced_media/arca2.20.2022/2022.02.20.07.57.08.avi"
cap = cv2.VideoCapture(path)
ret, frame = cap.read()
w, h = frame.shape[1], frame.shape[0]
fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
path = "C:/Users/Owner/Desktop/runway_detector (in progress)/produced_media/arca2.20.2022/2022.02.20.07.57.08_upside_down.avi"
fps = 30
out = cv2.VideoWriter(path,fourcc, fps, (w,h))

print("Flipping the video...")
while ret:
    ret, frame = cap.read()
    if ret == False:
        break
    frame = frame[::-1,::]
    out.write(frame)
    # cv2.imshow("frame", frame)
    # key = cv2.waitKey(1)
    # if key == ord('q'):
    #     break

print('Video flipping complete.')

cap.release()
out.release()
cv2.destroyAllWindows()


