import cv2
import numpy as np
from draw_horizon import draw_horizon
from math import pi

frame = np.zeros((720, 1280, 1), dtype = "uint8")
frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

full_rotation = 2 * pi
angle = 0
offset = .25
offset_direction = 1
while True:
    if angle > full_rotation * .75  or (angle > 0 and angle <= full_rotation * .25):
        sky_is_up = True
    else:
        sky_is_up = False
    frame_drawn = frame.copy()
    frame_drawn = draw_horizon(frame_drawn, angle, offset, True)
    cv2.imshow("frame", frame_drawn)
    key = cv2.waitKey(100)
    if key == ord('q'):
        break

    if offset > .75 or offset < .25:
        offset_direction = offset_direction * -1

    angle += .1
    angle = angle % full_rotation
    offset = offset + .01 * offset_direction

cv2.destroyAllWindows()