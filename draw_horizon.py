import cv2
import numpy as np
from math import cos, sin

def draw_horizon(frame, angle, offset_normalized, sky_is_up):
    # draw sky and ground lines
    height = frame.shape[0]
    width = frame.shape[1]
    line_width = int(frame.shape[0] * .03)
    if sky_is_up == 1:
        line_1_color = (255,0,0)
        line_2_color = (0,255,0)
    elif sky_is_up == 0:
        line_1_color = (0,255,0)
        line_2_color = (255,0,0)
    # draw top line (to indicate right side up or upside down)
    pt1 = (0, 0)
    pt2 = (width, 0)
    cv2.line(frame, pt1, pt2, line_1_color,line_width)
    # draw bottom line (to indicate right side up or upside down)
    pt1 = (0, height)
    pt2 = (width, height)
    cv2.line(frame, pt1, pt2, line_2_color,line_width)

    # draw the horizon
    offset = int(np.round(offset_normalized * frame.shape[0]))
    x = cos(angle)
    y = sin(angle) 
    m = y / x
    b = offset - m * .5 * frame.shape[1]
    # find the points to be drawn
    p1_x = 0
    p1_y = int(np.round(b)) # round so that we get an integer
    p1 = (p1_x, p1_y)
    p2_x = frame.shape[1]
    p2_y = int(np.round(m * frame.shape[1] + b))
    p2 = (p2_x, p2_y)
    frame = cv2.line(frame, p1, p2, (0,0,255), 2)
    return frame

if __name__ == "__main__":
    path = 'training_data/sample_images/2022.02.20.07.57.08_630.png'
    angle = 0.14514379644254055
    offset = 0.6491461716937355

    path = 'training_data/sample_images/sample_horizon.png'
    angle = 0.5478363265396572
    offset = 0.279784140969163

    frame = cv2.imread(path)
    sky_is_up = 1
    frame = draw_horizon(frame, angle, offset, sky_is_up)
    cv2.imshow("draw_horizon demo", frame)
    key = cv2.waitKey(0)
    if key == ord('q'):
        cv2.destroyAllWindows()
    