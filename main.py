import cv2
import time

from horizon_detector.video import CameraCapture

ITERATIONS = 500

# cap = CameraCapture()

# previous_frame = None
# t1 = time.time()
# for n in range(ITERATIONS):
#     print(n)
#     frame = cap.read()

#     cv2.waitKey(1)

# t2 = time.time()
# print(f'Time elapsed: {t2-t1} seconds.')
# print(f'FPS: {ITERATIONS/(t2-t1)}')

# cap.release()

# cv2.imwrite('test.jpg', frame)

# ITERATIONS = 1000
# cap = cv2.VideoCapture(0)

# t1 = time.time()
# for n in range(ITERATIONS):
#     ret, frame = cap.read()
#     # cv2.waitKey(1)
# t2 = time.time()
# print(frame.shape)
# print(f'Time elapsed: {t2-t1} seconds.')
# print(f'FPS: {ITERATIONS/(t2-t1)}')

import picamera
import time
import numpy as np

ITERATIONS = 500

with picamera.PiCamera() as camera:
    # Set camera resolution (optional)
    camera.resolution = (640, 480)
    
    # Warm-up the camera (optional, helps with exposure and white balance)
    time.sleep(2)
    
    frame = np.empty((480, 640, 3), dtype=np.uint8)
    t1 = time.time()
    for n in range(ITERATIONS):
        # Create a NumPy array to store the captured frame
        
        # Capture the frame directly into the array
        camera.capture(frame, 'rgb', use_video_port=True)
        
    t2 = time.time()

print(frame.shape)
print(f'Time elapsed: {t2 - t1} seconds.')
print(f'FPS: {ITERATIONS / (t2 - t1)}')


# from horizon_detector.utils import read_and_flatten_yaml

# # Read the configurations
# path = "configurations.yaml"
# config = read_and_flatten_yaml(path)
# print(config)