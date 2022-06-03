######## Horizon Detection Using Basic Image Processing #########
# Author: Tim Huff
# Date: 5/24/2022
# Description: 
# ...

import cv2
import numpy as np
from numpy.linalg import norm
from math import atan2, cos, sin, pi
from draw_horizon import draw_horizon
import global_variables as gv

FULL_ROTATION = 2 * pi

def adjust_angle(angle: float, sky_is_up: bool) -> float:
    """
    Adjusts the angle within the range of 0-2*pi
    """
    angle = abs(angle % FULL_ROTATION)
    in_sky_is_up_sector = (angle >= FULL_ROTATION * .75  or (angle > 0 and angle <= FULL_ROTATION * .25))
    
    if sky_is_up == in_sky_is_up_sector:
        return angle
    if angle < pi:
        angle += pi
    else:
        angle -= pi
    return angle

def find_horizon(frame:np.ndarray, 
                predicted_angle:float=None, predicted_offset:float=None, exclusion_thresh:float=None, 
                diagnostic_mode:bool=False) -> dict:
    """
    frame: the image in which you want to find the horizon
    predicted_angle: the predicted angle of the horizon based on previous frames
    predicted_offset: predicted offset of the horizon based on previous frames
    exclusion_thresh: parameter that controls how close horizon points have to be
    to predicted horizon in order to be considered valid
    """
    # initialize the horizon as None
    # if no horizon can be found, return this
    horizon = None
    # generate mask
    bgr2gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(bgr2gray,250,255,cv2.THRESH_OTSU)

    # find contours
    if gv.os == "Linux": # for raspberry pi
        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    else: # for windows
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return horizon # return None values for horizon

    # find the contour with the largest area
    largest_contour = sorted(contours, key=cv2.contourArea, reverse=True)[0] 

    # extract x and y values from contour
    x = np.array([i[0][0] for i in largest_contour])
    y = np.array([i[0][1] for i in largest_contour])

    # find the average position of the contours
    # this will help us determine the direction of the sky
    avg_x = np.average(x)
    avg_y = np.average(y)

    # remove points that lie near the corner of the frame
    bool_mask = np.logical_and(x > 2, x < (frame.shape[1] - 2))
    x = x[bool_mask]
    y = y[bool_mask]

    if diagnostic_mode and gv.render_image:
        # draw the unfiltered points 
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        for n, i in enumerate(x):
            circle_x = int(np.round(i))
            circle_y = int(np.round(y[n]))
            cv2.circle(mask, (circle_x, circle_y), 10, (0,0,255), 2)
        cv2.imshow("mask", mask)
        
    # if a previous horizon was provided, exclude any points from this
    # horizon that are too far away from the previous horizon
    if predicted_angle is not None:
        # convert from angle and offset of predicted horizon to m and b
        # convert from normalized offset to absolute offset
        predicted_offset_absolute = int(np.round(predicted_offset * frame.shape[0]))
        run = cos(predicted_angle)
        rise = sin(predicted_angle) 
        predicted_m = rise / run
        predicted_b = predicted_offset_absolute - predicted_m * .5 * frame.shape[1]

        # define two points on the line from the previous horizon
        p1 = np.array([0, predicted_b])
        p2 = np.array([frame.shape[1], predicted_m * frame.shape[1] + predicted_b])
        p2_minus_p1 = p2 - p1

        # initialize some lists to contain the new (filtered) x and y values
        x_filtered = []
        y_filtered = []

        # iterate over each point in this horizon and calculate its distance
        # from the previous horizon
        for n, x_point in enumerate(x):
            y_point = y[n]
            p3 = np.array([x_point, y_point])
            distance = norm(np.cross(p2_minus_p1, p1-p3))/norm(p2_minus_p1)
            if distance < exclusion_thresh:
                x_filtered.append(x_point)
                y_filtered.append(y_point)

        # redefine x and y with the new, filtered values, convert to numpy array
        x = np.array(x_filtered)
        y = np.array(y_filtered)

        if diagnostic_mode and gv.render_image:
            # draw the filtered points
            for n, i in enumerate(x):
                circle_x = int(np.round(i))
                circle_y = int(np.round(y[n]))
                cv2.circle(mask, (circle_x, circle_y), 10, (0,255,0), 2)
            mask = draw_horizon(mask, predicted_angle, predicted_offset, True)
            # draw the diagnostic mask
            cv2.imshow("mask", mask)
    
    if x.shape[0] < 5:
        # return None values for horizon, since too few points were found
        return horizon 

    # polyfit
    m, b = np.polyfit(x, y, 1)
    angle = atan2(m,1) 
    offset = (m * frame.shape[1]/2 + b) / frame.shape[1]

    # find the variance (this will be treated as a confidence score)
    yfit = np.polyval((m, b), x)
    variance = np.average(np.absolute(yfit - y)) / frame.shape[0] * 100

    # determine the direction of the sky (above or below)
    if m * avg_x + b > avg_y:
        sky_is_up = 1
    else:
        sky_is_up = 0

    # adjust the angle within the range of 0-2*pi
    angle = adjust_angle(angle, sky_is_up)

    # print(f'angle: {angle} | offset: {offset} | sky_is_up: {sky_is_up}')

    # put horizon values into a dictionary
    horizon = {}
    horizon['angle'] = angle
    horizon['offset'] = offset
    # horizon['sky_is_up'] = sky_is_up
    horizon['variance'] = variance
    horizon['m'] = m
    horizon['b'] = b

    # return the calculated values for horizon
    return horizon 

if __name__ == "__main__":
    # load the image
    path = 'training_data/sample_images/sample_horizon.png'
    frame = cv2.imread(path)

    # define some variables related to cropping and scaling
    from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
    INFERENCE_RESOLUTION = (100, 100)
    resolution = frame.shape[1::-1] # extract the resolution from the frame

    # scale the images down
    crop_and_scale_param = get_cropping_and_scaling_parameters(resolution, INFERENCE_RESOLUTION)
    frame_small = crop_and_scale(frame, **crop_and_scale_param)

    # find the horizon
    horizon = find_horizon(frame_small, diagnostic_mode=True)
    angle = horizon['angle'] 
    offset = horizon['offset'] 
    variance = horizon['variance'] 
    m = horizon['m'] 
    b = horizon['b'] 

    # draw the horizon
    frame = draw_horizon(frame, angle, offset, True)

    # show results
    cv2.imshow("frame", frame)
    cv2.waitKey(0)