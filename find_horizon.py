######## Horizon Detection Using Basic Image Processing #########
# Author: Tim Huff

import cv2
import numpy as np
from numpy.linalg import norm
from math import atan2, cos, sin, pi, sqrt
from draw_display import draw_horizon
import global_variables as gv

FULL_ROTATION = 2 * pi

def adjust_angle(angle: float, sky_is_up: bool) -> float:
    """
    Adjusts the angle within the range of 0-2*pi
    Removes negative values and values greater than 2*pi
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

    # generate mask
    bgr2gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(bgr2gray,9,100,100)
    _, mask = cv2.threshold(blur,250,255,cv2.THRESH_OTSU)
    # mask = cv2.adaptiveThreshold(bgr2gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)

    # find contours
    if gv.os == "Linux": # for raspberry pi
        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    else: # for windows
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize the horizon as a dictionary of None values.
    # If no horizon can be found, this will be returned.
    horizon = {}
    horizon['angle'] = None
    horizon['offset'] = None
    horizon['offset_new'] = None
    horizon['variance'] = None
    horizon['m'] = None
    horizon['b'] = None

    if len(contours) == 0:
        # If there are too few contours to find a horizon,
        # return a dictionary of None values
        return horizon 

    # find the contour with the largest area
    largest_contour = sorted(contours, key=cv2.contourArea, reverse=True)[0] 

    # extract x and y values from contour
    x_original = np.array([i[0][0] for i in largest_contour])
    y_original = np.array([i[0][1] for i in largest_contour])

    # find the average position of the contours
    # this will help us determine the direction of the sky
    avg_x = np.average(x_original)
    avg_y = np.average(y_original)

    # reduce the number of points to improve performance
    maximum_number_of_points = 30
    step_size = len(x_original)//maximum_number_of_points
    if step_size > 1:
        x_abbr = x_original[::step_size]
        y_abbr = y_original[::step_size]
    else:
        x_abbr = x_original
        y_abbr = y_original
    
    # remove points that lie near the corner of the frame
    bool_mask = np.logical_and(x_abbr > 2, x_abbr < (frame.shape[1] - 2))
    x_abbr = x_abbr[bool_mask]
    y_abbr = y_abbr[bool_mask]
    
#     # WORK IN PROGRESS
#     # remove corner points
#     x_list = []
#     y_list = []
#     for idx, x_point in enumerate(x_abbr):
#         y_point = y_abbr[idx]
#         upper_left = x_point == 0 and 
#         if not any([x_point == 0, x_point == frame.shape[1], y_point == 0, y_point == frame.shape[0]]):
#             x_list.append(x_point)
#             y_list.append(y_point)
#     x_abbr = np.array(x_list)
#     y_abbr = np.array(y_list)            
        
    # if a previous horizon was provided, exclude any points from this
    # horizon that are too far away from the previous horizon
    if predicted_angle is None:
        x_filtered = x_abbr
        y_filtered = y_abbr
    else:
        # initialize some lists to contain the new (filtered) x and y values
        x_filtered = []
        y_filtered = []

        # convert predicted angle to radians
        predicted_angle = predicted_angle * 2 * pi

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

        # Iterate over each point in this horizon and calculate its distance
        # from the previous horizon.
        for idx, x_point in enumerate(x_abbr):
            y_point = y_abbr[idx]
            p3 = np.array([x_point, y_point])
            distance = norm(np.cross(p2_minus_p1, p1-p3))/norm(p2_minus_p1)
            if distance < exclusion_thresh:
                x_filtered.append(x_point)
                y_filtered.append(y_point)

        # convert to numpy array
        x_filtered = np.array(x_filtered)
        y_filtered = np.array(y_filtered)

    # Draw the diagnostic information.
    # Only use for diagnostics, as this slows down inferences. 
    if diagnostic_mode and gv.render_image:
        # scale up the image to make it easier to see
        desired_height = 500
        scale_factor = desired_height / frame.shape[0]
        desired_width = int(np.round(frame.shape[1] * scale_factor))
        desired_dimensions = (desired_width, desired_height)
        mask = cv2.resize(mask, desired_dimensions)
        bgr2gray = cv2.resize(bgr2gray, desired_dimensions)
        blur = cv2.resize(blur, desired_dimensions)
        # convert the mask to color
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # draw the original points
        for n, i in enumerate(x_original):
            circle_x = int(np.round(i * scale_factor))
            circle_y = int(np.round(y_original[n] * scale_factor))
            cv2.circle(mask, (circle_x, circle_y), 10, (255,0,0), 2)
        # draw the abbreviated points
        for n, i in enumerate(x_abbr):
            circle_x = int(np.round(i * scale_factor))
            circle_y = int(np.round(y_abbr[n] * scale_factor))
            cv2.circle(mask, (circle_x, circle_y), 10, (0,0,255), 2)
        # draw the filtered points
        for n, i in enumerate(x_filtered):
            circle_x = int(np.round(i * scale_factor))
            circle_y = int(np.round(y_filtered[n] * scale_factor))
            cv2.circle(mask, (circle_x, circle_y), 10, (0,255,0), 2)
        # draw the predicted horizon, if there is one
        if predicted_angle:
            # normalize the angle
            predicted_angle = predicted_angle / (2 * pi)
            mask = draw_horizon(mask, predicted_angle, predicted_offset, 0,  False)
        
        # draw the results
        cv2.imshow("mask", mask)
        cv2.imshow("bgr2gray", bgr2gray)
        cv2.imshow("blur", blur)
    
    # Return None values for horizon, since too few points were found.
    if x_filtered.shape[0] < 3:
        return horizon 

    # polyfit
    m, b = np.polyfit(x_filtered, y_filtered, 1)
    angle = atan2(m,1)
    offset = (m * frame.shape[1]/2 + b) / frame.shape[0]

    # determine the direction of the sky (above or below)
    if m * avg_x + b > avg_y:
        sky_is_up = 1 # above
    else:
        sky_is_up = 0 # below

    # FIND PITCH 
    # define two points along horizon
    p1 = np.array([0, b])
    p2 = np.array([frame.shape[1], m * frame.shape[1] + b])
    # center of the image
    p3 = np.array([frame.shape[1]//2, frame.shape[0]//2]) 
    frame_diagonal = sqrt(frame.shape[0]**2 + frame.shape[1]**2)
    # find out if plane is pointing above or below horizon
    if p3[1] < m * frame.shape[1]//2 + b and sky_is_up:
        plane_pointing_up = 1
    elif p3[1] > m *frame.shape[1]//2 + b and sky_is_up == False:
        plane_pointing_up = 1
    else:
        plane_pointing_up = 0

    distance_to_horizon = norm(np.cross(p2-p1, p1-p3))/norm(p2-p1) / frame_diagonal
    if plane_pointing_up:
        offset_new = .5 - distance_to_horizon
    else:
        offset_new = .5 + distance_to_horizon

    # FIND VARIANCE 
    # (this will be treated as a confidence score)
    p1 = np.array([0, b])
    p2 = np.array([frame.shape[1], m * frame.shape[1] + b])
    p2_minus_p1 = p2 - p1
    distance_list = []
    for n, x_point in enumerate(x_filtered):
        y_point = y_filtered[n]
        p3 = np.array([x_point, y_point])
        distance = norm(np.cross(p2_minus_p1, p1-p3))/norm(p2_minus_p1)
        distance_list.append(distance)
    variance = np.average(distance_list) / frame.shape[0] * 100
    
    # adjust the angle within the range of 0-2*pi
    angle = adjust_angle(angle, sky_is_up) 

    # normalize the angle
    angle = angle / (2 * pi)

    # put horizon values into a dictionary
    horizon = {}
    horizon['angle'] = angle
    horizon['offset'] = offset
    horizon['offset_new'] = offset_new
    horizon['variance'] = variance
    horizon['m'] = m
    horizon['b'] = b

    # return the calculated values for horizon
    return horizon 

def get_pitch(offset: float, inf_fov_diag: float) -> float:
    """
    Takes the normalized offset and returns the pitch in degrees
    based on the diagonal field of view of the inference image (inf_fov_diag).
    """
    if offset is None:
        return None

    # shift the normalized offset to an offset range -1 to 1
    offset_pos_neg = 2 * offset - 1 
    return -1 * offset_pos_neg * inf_fov_diag / 2

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