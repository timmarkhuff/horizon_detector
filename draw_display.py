import cv2
import numpy as np
from math import cos, sin, pi, degrees, sqrt

FULL_ROTATION = 2 * pi

def draw_roi(frame: np.ndarray, crop_and_scale_parameters: dict) -> np.ndarray:
    """
    Draws the region of interest onto the frame, i.e. the region where 
    horizon detection occurs.

    frame: the frame to draw on
    crop_and_scale_parameters: parameters obtained by crop_and_scale.get_cropping_and_scaling_parameters
    """
    # extract some relevant values from the dictionary
    cropping_start= crop_and_scale_parameters['cropping_start']
    cropping_end = crop_and_scale_parameters['cropping_end']
    p1 = (cropping_start, 0)
    p2 = (cropping_start, frame.shape[1])
    p3 = (cropping_end, 0)
    p4 = (cropping_end, frame.shape[1])

    # define the color
    off_white = (215, 215, 215)

    # draw the lines
    cv2.line(frame, p1, p2, off_white, 1)
    cv2.line(frame, p3, p4, off_white, 1)


def draw_hud(frame: np.ndarray, angle:float , pitch: float, fps: float,
                is_good_horizon: bool, recording: bool = False) -> np.ndarray:
    # draw angle and pitch text
    if angle and is_good_horizon:
        angle_degrees = degrees(angle * 2 * pi)
        angle_degrees = int(np.round(angle_degrees))
        pitch = int(np.round(pitch))
        color = (255, 0, 0)
    else:
        angle_degrees = ''
        pitch = ''
        color = (0,0,255)
    # round fps
    fps = np.round(fps, decimals=2)
    cv2.putText(frame, f"Roll: {angle_degrees}",(20,40),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)
    cv2.putText(frame, f"Pitch: {pitch}",(20,80),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)
    cv2.putText(frame, f"FPS: {fps}",(20,120),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(255,0,0),1,cv2.LINE_AA)

    # draw recording text
    if recording:
        position = (frame.shape[1] - 140, 40)
        color = (0,0,255)
        cv2.putText(frame, "Recording", position,cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)

    return frame

def draw_horizon(frame: np.ndarray, angle:float , offset_normalized: float, 
                    color: tuple, draw_groundline: bool):

    # if no horizon data is provided, terminate function early and
    # return provided frame
    if angle is None:
        return frame

    # take normalized angle and express it in terms of radians
    angle = angle * 2 * pi
    
    # determine if the sky is up or down based on the angle
    sky_is_up = (angle >= FULL_ROTATION * .75  or (angle > 0 and angle <= FULL_ROTATION * .25))

    # define the horizon line
    offset = int(np.round(offset_normalized * frame.shape[0]))
    x = cos(angle)
    y = sin(angle) 
    m = y / x
    b = offset - m * .5 * frame.shape[1]
    p1_x = 0
    p1_y = int(np.round(b)) # round so that we get an integer
    p1_horizon = (p1_x, p1_y)
    p2_x = frame.shape[1]
    p2_y = int(np.round(m * frame.shape[1] + b))
    p2_horizon = (p2_x, p2_y)


    # define the ground line
    if draw_groundline:
        m_groundline = -1/m
        b_groundline = frame.shape[0]//2 - m_groundline * frame.shape[1]//2
        # find the points to be drawn
        p1_x = int(np.round((b_groundline - b) / (m - m_groundline)))
        p1_y = int(np.round(m * p1_x + b))
        p1 = (p1_x, p1_y)
        if sky_is_up:
            p2_y = frame.shape[0]
            p2_x = int(np.round((p2_y - b_groundline) / m_groundline))
        else:
            p2_y = 0
            p2_x = int(np.round(-1 * b_groundline / m_groundline))
        p2 = (p2_x, p2_y)
        # draw the ground line
        cv2.line(frame, p1, p2, (0,191,255), 1)

    # draw the horizon
    cv2.line(frame, p1_horizon, p2_horizon, color, 2)

def draw_servos(frame: np.ndarray, aileron_value) -> np.ndarray:
    # define lengths and widths for drawing
    hor_offset = int(frame.shape[1] * .03)
    ver_offset = int(frame.shape[0] * .95)
    wingspan = int(frame.shape[1] * .3)
    vert_stab_height = int(frame.shape[1] * .05)
    hor_stab_width = int(frame.shape[0] * .15)
    hor_stab_height = int(frame.shape[1] * .02)
    aileron_width = int(frame.shape[1] * .06)
    aileron_offset = int(frame.shape[1] * .02)
    full_deflection = int(frame.shape[1] * .02)

    if not aileron_value:
        aileron_value = 0

    # define values related to servos
    center_value = 0
    max_deflection = 1
    value_diff = aileron_value - center_value
    value_diff_norm = value_diff / max_deflection

    # draw wing
    pt1 = (hor_offset, ver_offset)
    pt2 = (hor_offset + wingspan, ver_offset)
    cv2.line(frame, pt1, pt2, (0,0,200), 2)

    # draw vertical stabilizer
    x = int(hor_offset + wingspan/2)
    y = ver_offset
    pt1 = (x, y)
    x = int(hor_offset + wingspan/2)
    y = ver_offset - vert_stab_height
    pt2 = (x, y)
    cv2.line(frame, pt1, pt2, (0,0,200), 2)

    # draw horizontal stabilizer
    x = int(hor_offset + wingspan/2 - hor_stab_width/2)
    y = ver_offset - hor_stab_height
    pt1 = (x, y)
    x = int(hor_offset + wingspan/2 + hor_stab_width/2)
    y = ver_offset - hor_stab_height
    pt2 = (x, y)
    cv2.line(frame, pt1, pt2, (0,0,200), 2)
    
    # draw left aileron
    x = int(hor_offset + aileron_offset)
    y = int(ver_offset + full_deflection * value_diff_norm)
    pt1 = (x, y)
    x = int(hor_offset + aileron_offset + aileron_width)
    y = ver_offset
    pt2 = (x, y)
    cv2.rectangle(frame, pt1, pt2, (0,200,200), -1)
    cv2.rectangle(frame, pt1, pt2, (0,200,200), 2)

    # draw right aileron
    x = int(hor_offset + wingspan - aileron_offset)
    y = int(ver_offset - full_deflection * value_diff_norm)
    pt1 = (x, y)
    x = int(hor_offset + wingspan - aileron_offset - aileron_width)
    y = ver_offset
    pt2 = (x, y)
    cv2.rectangle(frame, pt1, pt2, (0,200,200), -1)
    cv2.rectangle(frame, pt1, pt2, (0,200,200), 2)

    return frame
    