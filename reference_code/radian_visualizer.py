import cv2
import numpy as np
from draw_display import draw_horizon, draw_hud
from math import pi

frame = np.zeros((720, 1280, 1), dtype = "uint8")
frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

def make_not_zero(number):
    if number != 0:
        return number
    else:
        return .000001

FULL_ROTATION = 2 * pi
angle = .1
offset = .25
offset_direction = 1
while True:
    if angle > FULL_ROTATION * .75  or (angle > 0 and angle <= FULL_ROTATION * .25):
        sky_is_up = True
    else:
        sky_is_up = False
    frame_drawn = frame.copy()
    try:
        frame_drawn = draw_horizon(frame_drawn, angle, offset, True)
        frame_drawn = draw_hud(frame_drawn, angle, offset, True)
    except:
        pass
    cv2.imshow("frame", frame_drawn)
    key = cv2.waitKey(100)
    if key == ord('q'):
        break

    if offset > .75 or offset < .25:
        offset_direction = offset_direction * -1

    angle += .01
    angle = make_not_zero(angle % FULL_ROTATION)
    offset = offset + .01 * offset_direction

cv2.destroyAllWindows()