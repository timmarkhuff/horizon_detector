import cv2
import numpy as np
from math import atan2
from draw_horizon import draw_horizon

def find_horizon(frame, previous_horizon=None):

    # generate mask
    bgr2gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(bgr2gray,250,255,cv2.THRESH_OTSU)

    # find contours
    try: # for window
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    except: # for raspberry pi
        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 

    if len(contours) != 0:
        largest_contour = sorted(contours, key=cv2.contourArea, reverse=True)[0] # find the contour with the largest area

        # extract x and y values from contour
        if previous_horizon is None:
            x = np.array([i[0][0] for i in largest_contour])
            y = np.array([i[0][1] for i in largest_contour])
            x_unfiltered = x
            y_unfiltered = y

        # find the average position of the contours
        # this will help us determine the direction of the sky
        avg_x = np.average(x_unfiltered)
        avg_y = np.average(y_unfiltered)

        # remove points that lie near the corner of the frame
        bool_mask = np.logical_and(x > 2, x < (frame.shape[1] - 2))
        x = x[bool_mask]
        y = y[bool_mask]
    
    # # draw the points (diagnostic)
    # mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    # for n, i in enumerate(x_unfiltered):
    #     circle_x = int(np.round(i))
    #     circle_y = int(np.round(y_unfiltered[n]))
    #     cv2.circle(mask, (circle_x, circle_y), 10, (0,0,255), 2)
    # for n, i in enumerate(x):
    #     circle_x = int(np.round(i))
    #     circle_y = int(np.round(y[n]))
    #     cv2.circle(mask, (circle_x, circle_y), 10, (0,0,255), 2)
    # cv2.imshow("mask", mask)
 
    # polyfit
    m, b = np.polyfit(x, y, 1)
    angle = atan2(m,1)
    offset = (m * frame.shape[1]/2 + b) / frame.shape[1]
    sky_is_up = 1

    # filter out bad points

    # define horizon
    horizon = (angle, offset, sky_is_up)

    return horizon

if __name__ == "__main__":
    from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
    DESIRED_WIDTH = 100
    DESIRED_HEIGHT = 100
    path = 'training_data/sample_images/sample_horizon_corrected.png'
    frame = cv2.imread(path)
    cropping_start, cropping_end, scale_factor = get_cropping_and_scaling_parameters(frame, DESIRED_WIDTH, DESIRED_HEIGHT)
    frame_small = crop_and_scale(frame, cropping_start, cropping_end, scale_factor)
    angle, offset, sky_is_up = find_horizon(frame_small)
    frame = draw_horizon(frame, angle, offset, sky_is_up)
    frame_small = draw_horizon(frame_small, angle, offset, sky_is_up)
    cv2.imshow("frame_small", frame_small)
    cv2.imshow("frame", frame)
    cv2.waitKey(0)