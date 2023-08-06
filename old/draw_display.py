import cv2
import numpy as np
from math import cos, sin, pi, radians

FULL_ROTATION = 360
FULL_ROTATION_RADIANS = 2 * pi

def _restrict(val, upper_bound:float=1, lower_bound:float=-1):
    """
    Restricts the provided value with the provided upper bound and lower bound
    """
    if val > upper_bound:
        val = upper_bound
    elif val < lower_bound:
        val = lower_bound
    return val

def _find_points(m: float, b: float, frame_shape: tuple) -> list:
    """"
    Given the slope (m), y intercept (b) and the frame shape (frame_shape),
    find the two points of the line that intersect with the border of the frame.
    """
    # special condition if slope is 0
    if m == 0:
        b = int(np.round(b))
        p1 = (0, b)
        p2 = (frame_shape[1], b)
        return [p1, p2]

    points_to_return = []
    # left
    if 0 < b <= frame_shape[0]:
        px = 0
        py = int(np.round(b))
        points_to_return.append((px, py))
    # top
    if 0 < -b / m <= frame_shape[1]:
        px = int(np.round(-b / m))
        py = 0
        points_to_return.append((px, py))
    # right
    if 0 < m * frame_shape[1] + b <= frame_shape[0]:
        px = frame_shape[1]
        py = int(np.round(m * frame_shape[1] + b))
        points_to_return.append((px, py))
    # bottom
    if 0 < (frame_shape[0] - b) / m <= frame_shape[1]:
        px = int(np.round((frame_shape[0] - b) / m))
        py = frame_shape[0]
        points_to_return.append((px, py))

    return points_to_return

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


def draw_hud(frame: np.ndarray, roll: float , pitch: float, fps: float,
                is_good_horizon: bool, recording: bool = False) -> np.ndarray:
    # draw roll and pitch text
    if roll and is_good_horizon:
        roll = int(np.round(roll))
        pitch = int(np.round(pitch))
        color = (255, 0, 0)
    else:
        roll = ''
        pitch = ''
        color = (0,0,255)
    # round fps
    fps = np.round(fps, decimals=2)
    cv2.putText(frame, f"Roll: {roll}",(20,40),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)
    cv2.putText(frame, f"Pitch: {pitch}",(20,80),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)
    cv2.putText(frame, f"FPS: {fps}",(20,120),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(255,0,0),1,cv2.LINE_AA)

    # draw recording text
    if recording:
        position = (frame.shape[1] - 140, 40)
        color = (0,0,255)
        cv2.putText(frame, "Recording", position,cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)

    return frame

def draw_horizon(frame: np.ndarray, roll: float , pitch: float, 
                    fov: float, color: tuple, draw_groundline: bool):

    # if no horizon data is provided, terminate function early and return
    if roll is None:
        return

    # take roll in degrees and express it in terms of radians
    roll = radians(roll)
    
    # determine if the sky is up or down based on the roll
    sky_is_up = (roll >= FULL_ROTATION_RADIANS * .75  or (roll > 0 and roll <= FULL_ROTATION_RADIANS * .25))
    
    # find the distance 
    distance = pitch / fov * frame.shape[0]

    # define the line perpendicular to horizon
    angle_perp = roll + pi / 2
    x_perp = distance * cos(angle_perp) + frame.shape[1]/2
    y_perp = distance * sin(angle_perp) + frame.shape[0]/2

    # define the horizon line
    run = cos(roll)
    rise = sin(roll)
    if run != 0:
        m = rise / run
        b = y_perp - m * x_perp
        points = _find_points(m, b, frame.shape)
        if not points:
            return
        else:
            p1, p2 = points
       
    else:
        p1 = (int(np.round(x_perp)), 0)
        p2 = (int(np.round(x_perp)), frame.shape[0])

    cv2.line(frame, p1, p2, color, 2)

    if draw_groundline and m != 0:
        m_perp = -1/m
        b_perp = y_perp - m_perp * x_perp
        points = _find_points(-1/m, b_perp, frame.shape)
        above_line = m * points[0][0] + b < points[0][1]
        if (sky_is_up and above_line) or (not sky_is_up and not above_line):
            p2 = points[0]
        else:
            p2 = points[1]
        p1x = int(np.round(x_perp))
        p1y = int(np.round(y_perp))
        p1 = (p1x, p1y)
        cv2.line(frame, p1, p2, (0,191,255), 1)

def draw_surfaces(frame, left: float, right: float, top: float, bottom: float, 
                    ail_val: float, elev_val: float, surface_color: tuple):
    # constants
    plane_color = (50, 50, 50)
    plane_thickness = 3

    # convert to pixel values, relative to frame size
    left = int(np.round(frame.shape[1] * left))
    right = int(np.round(frame.shape[1] * right))
    top = int(np.round(frame.shape[0] * top))
    bottom = int(np.round(frame.shape[0] * bottom))
    plane_width = right - left
    plane_height = bottom - top
    hor_stab_height = int(np.round(.6 * plane_height))
    hor_stab_width = int(np.round(.4 * plane_width))
    full_defection = int(np.round(.2 * plane_height))
    ail_width = plane_width//3
    ail_offset = plane_width//20
    elev_offset = ail_offset

    # draw wing
    pt1 = (left, bottom)
    pt2 = (right, bottom)
    cv2.line(frame, pt1, pt2, plane_color, plane_thickness)

    # draw vertical stabilizer
    pt1 = (left + plane_width//2, top)
    pt2 = (left + plane_width//2, bottom)
    cv2.line(frame, pt1, pt2, plane_color, plane_thickness)

    # draw horizontal stabilizer
    pt1x = left + plane_width//2 - hor_stab_width//2
    pt1y = top + plane_height - hor_stab_height
    pt1 = (pt1x , pt1y)
    pt2x = right - plane_width//2 + hor_stab_width//2
    pt2y = pt1y
    pt2 = (pt2x, pt2y)
    cv2.line(frame, pt1, pt2, plane_color, plane_thickness)

    # If there are no surface values to draw, return early
    if None in (ail_val, elev_val):
        return

    # draw elevator
    elev_deflection = int(np.round(elev_val * full_defection))
    pt1x = left + plane_width//2 - hor_stab_width//2 + elev_offset
    pt1y = top + plane_height - hor_stab_height - elev_deflection
    pt1 = (pt1x , pt1y)
    pt2x = right - plane_width//2 + hor_stab_width//2 - elev_offset
    pt2y = top + plane_height - hor_stab_height
    pt2 = (pt2x, pt2y)
    cv2.rectangle(frame, pt1, pt2, surface_color, -1)

    # draw ailerons
    # left
    ail_deflection = int(np.round(ail_val * full_defection))
    pt1 = (left + ail_offset, bottom)
    pt2 = (left + ail_offset + ail_width, bottom - ail_deflection)
    cv2.rectangle(frame, pt1, pt2, surface_color, -1)

    # right
    pt1 = (right - ail_offset, bottom)
    pt2 = (right - ail_offset - ail_width, bottom + ail_deflection)
    cv2.rectangle(frame, pt1, pt2, surface_color, -1)

def draw_stick(frame, left: float, top: float, width: float, 
                val1: float, val2: float, trim1: float, trim2: float, color: tuple):

    # general variables
    height = width
    width_pixels = width * frame.shape[1]
    height_pixels = width_pixels
    left_pixels = left * frame.shape[1]
    right_pixels = (left + width) * frame.shape[1]
    top_pixels = top * frame.shape[0]

    # draw outer circle
    outer_circle_color = (80,80,80)
    radius_pixels = (right_pixels - left_pixels)/2
    center_x = left_pixels + radius_pixels
    center_y = top_pixels + radius_pixels
    center_rounded = (round(center_x), round(center_y))
    cv2.circle(frame, center_rounded, round(radius_pixels), outer_circle_color, -1)

    # draw crosslines
    crossline_color = (245,245,245)
    crossline_width = 1
    # line 1
    hor_offset_from_center = width_pixels * .4
    pt1x = center_x - hor_offset_from_center
    pt1y = center_y 
    pt2x = center_x + hor_offset_from_center
    pt2y = center_y
    pt1 = (round(pt1x), round(pt1y))
    pt2 = (round(pt2x), round(pt2y))
    cv2.line(frame, pt1, pt2, crossline_color, crossline_width)

    # line 2
    vert_offset_from_center = height_pixels * .4
    pt1x = center_x 
    pt1y = center_y - vert_offset_from_center
    pt2x = center_x 
    pt2y = center_y + vert_offset_from_center
    pt1 = (round(pt1x), round(pt1y))
    pt2 = (round(pt2x), round(pt2y))
    cv2.line(frame, pt1, pt2, crossline_color, crossline_width)

    # draw inner rectangle
    hor_offset_from_center = height_pixels * .3
    vert_offset_from_center = height_pixels * .21
    rectangle_color = (40,40,40)
    pt1x = center_x - hor_offset_from_center
    pt1y = center_y - vert_offset_from_center
    pt2x = center_x + hor_offset_from_center
    pt2y = center_y + vert_offset_from_center
    rectangle_width = pt2x - pt1x
    pt1 = (round(pt1x), round(pt1y))
    pt2 = (round(pt2x), round(pt2y))
    cv2.rectangle(frame, pt1, pt2, rectangle_color, -1)

    # Restrict stick values within acceptable bounds (-1, 1)
    val1 = _restrict(val1)
    val2 = _restrict(val2)
    trim1 = _restrict(trim1)
    trim2 = _restrict(trim2)

    # Draw stick
    stick_color = (230,230,230)
    stick_width = height_pixels * .12
    pt1x = center_x
    pt1y = center_y
    pt2x = center_x + val1 * rectangle_width/2
    pt2y = center_y + val2 * rectangle_width/2
    pt1 = (round(pt1x), round(pt1y)) # base of stick
    pt2 = (round(pt2x), round(pt2y)) # tip of stick
    cv2.line(frame, pt1, pt2, stick_color, round(stick_width))

    # Draw tip of stick
    cv2.circle(frame, pt2, round(stick_width/2), outer_circle_color, -1)
    cv2.circle(frame, pt2, round(stick_width/2), color, 2)



    
