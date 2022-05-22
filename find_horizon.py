import cv2
import numpy as np
from numpy.linalg import norm
from math import atan2
from draw_horizon import draw_horizon

def find_horizon(frame, previous_m=None, previous_b=None, exclusion_thresh=None):
    # initialize some None values for horizon, we will
    # return these if no horizon can be found
    horizon = (None, None, None, None, None, None)
    # generate mask
    bgr2gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(bgr2gray,250,255,cv2.THRESH_OTSU)

    # find contours
    try: # for windows
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    except: # for raspberry pi
        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 

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

    # draw the unfiltered points (diagnostic)
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    for n, i in enumerate(x):
        circle_x = int(np.round(i))
        circle_y = int(np.round(y[n]))
        cv2.circle(mask, (circle_x, circle_y), 10, (0,0,255), 2)
    cv2.imshow("mask", mask)

    # if a previous horizon was provided, exclude any points from this
    # horizon that are too far away from the previous horizon
    if previous_m is not None:
        # define two points on the line from the previous horizon
        p1 = np.array([0, previous_b])
        p2 = np.array([frame.shape[1], previous_m * frame.shape[1] + previous_b])
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

        # draw the filtered points (diagnostic)
        for n, i in enumerate(x):
            circle_x = int(np.round(i))
            circle_y = int(np.round(y[n]))
            cv2.circle(mask, (circle_x, circle_y), 10, (0,255,0), 2)
    
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

    # define horizon
    horizon = (angle, offset, sky_is_up, variance, m, b)

    # return the calculated values for horizon
    return horizon 

if __name__ == "__main__":
    # load the images
    path = 'training_data/sample_images/sample_horizon_corrected.png'
    horizon_flawless = cv2.imread(path)
    path = 'training_data/sample_images/sample_horizon.png'
    horizon_flawed = cv2.imread(path)

    # define some variables related to cropping and scaling
    from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
    DESIRED_WIDTH = 100
    DESIRED_HEIGHT = 100
    EXCLUSION_THRESH = horizon_flawless.shape[1] * .075

    # scale the images down
    cropping_start, cropping_end, scale_factor = get_cropping_and_scaling_parameters(horizon_flawless, DESIRED_WIDTH, DESIRED_HEIGHT)
    horizon_flawless_small = crop_and_scale(horizon_flawless, cropping_start, cropping_end, scale_factor)
    horizon_flawed_small = crop_and_scale(horizon_flawed, cropping_start, cropping_end, scale_factor)

    # find the first horizon
    angle, offset, sky_is_up, variance, m, b = find_horizon(horizon_flawless_small)
    previous_m = m
    previous_b = b
    print(f'variance: {variance}')

    # find the next horizon
    angle_2, offset_2, sky_is_up_2, variance_2, m_2, b_2 = find_horizon(horizon_flawed_small, previous_m, previous_b, EXCLUSION_THRESH)
    print(f'variance: {variance_2}')

    # draw the horizon
    horizon_flawless = draw_horizon(horizon_flawless, angle, offset, sky_is_up)
    horizon_flawed = draw_horizon(horizon_flawed, angle_2, offset_2, sky_is_up_2)

    # show results
    cv2.imshow("horizon_flawless", horizon_flawless)
    cv2.imshow("horizon_flawed", horizon_flawed)
    cv2.waitKey(0)