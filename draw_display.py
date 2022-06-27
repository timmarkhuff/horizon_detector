import cv2
import numpy as np
from math import cos, sin, pi, degrees

FULL_ROTATION = 2 * pi

def draw_hud(frame: np.ndarray, angle:float , offset_normalized: float, 
                is_good_horizon: bool, recording: bool = False) -> np.ndarray:
    # draw angle
    if angle and is_good_horizon:
        angle_degrees = degrees(angle * 2 * pi)
        angle_degrees = int(np.round(angle_degrees))
        color = (255, 0, 0)
    else:
        angle_degrees = ''
        color = (0,0,255)
    cv2.putText(frame, f"Angle: {angle_degrees}",(20,40),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)

    # draw center circle
    x = frame.shape[1]//2
    y = frame.shape[0]//2
    center = (x, y)
    radius = frame.shape[0]//72
    cv2.circle(frame, center, radius, (255,0,0), 2)

    # draw recording text
    if recording:
        position = (frame.shape[1] - 140, 40)
        color = (0,0,255)
        cv2.putText(frame, "Recording", position,cv2.FONT_HERSHEY_COMPLEX_SMALL,1,color,1,cv2.LINE_AA)

    return frame

def draw_horizon(frame: np.ndarray, angle:float , offset_normalized: float, is_good_horizon: bool) -> np.ndarray:
    # if no horizon data is provided, terminate function early and
    # return provided frame
    if angle is None:
        return frame

    # take normalized angle and express it in terms of radians
    angle = angle * 2 * pi
    
    if is_good_horizon:
        horizon_color = (255,0,0)
    else:
        horizon_color = (0,0,255)

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
    if is_good_horizon:
        m_groundline = -1/m
        b_groundline = frame.shape[0]//2 - m_groundline * frame.shape[1]//2
        # b = offset - m * .5 * frame.shape[1]
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
        frame = cv2.line(frame, p1, p2, (0,191,255), 1)

    # draw the horizon
    frame = cv2.line(frame, p1_horizon, p2_horizon, horizon_color, 2)

    return frame

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

if __name__ == "__main__":
    path = 'training_data/sample_images/sample_horizon.png'
    frame = cv2.imread(path)
    frame = draw_servos(frame, 6)
    cv2.imshow("Servos", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # # Horizon Demonstration
    # path = 'training_data/sample_images/sample_horizon.png'
    # angle = 0.5478363265396572
    # offset = 0.279784140969163
    # good_horizon = True
    # frame = cv2.imread(path)
    # frame = draw_horizon(frame, angle, offset, good_horizon)
    # cv2.imshow("draw_horizon demo", frame)
    # key = cv2.waitKey(0)
    # if key == ord('q'):
    #     cv2.destroyAllWindows()
    