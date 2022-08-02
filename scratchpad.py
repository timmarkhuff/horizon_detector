import cv2
import numpy as np
from math import cos, sin, radians
from time import sleep

def find_points(m, b, frame_shape) -> list:
    """
    Takes the slope (m) and y intercept (b) of a line and 
    the shape of the frame (frame_shape) to draw on.

    Returns a list of the two endpoints of the line, such that 
    the points intersect with the border of the frame.
    """
    if m == 0:
        return None, None

    y_coord_candidates = [frame_shape[0], 0]
    points_to_return = []
    for y in y_coord_candidates:
        x = (y - b) / m
        if x >= 0 and x <= frame_shape[1]:
            pass
        elif x < 0:
            y = b
            x = 0
        elif x > frame_shape[1]:
            x = frame_shape[1]
            y = m * x + b
        pt = (int(np.round(x)), int(np.round(y))) # round the coordinates so they can be drawn
        points_to_return.append(pt)
    return points_to_return


def main():
    canvas = np.zeros((500, 1000, 3), dtype = "uint8")

    # center point
    x = canvas.shape[1] // 2
    y = canvas.shape[0] // 2
    center = (x, y)
    cv2.circle(canvas, center, 10, (255,0,0),2)
    
    # https://www.wyzant.com/resources/answers/601887/calculate-point-given-x-y-angle-and-distance
    # If your starting point is (0,0), and your new point is r units away at an angle of θ, 
    # you can find the coordinates of that point using the equations x = r cosθ and y = r sinθ.  
    # These are the standard equations that let you convert from the 
    # rectangular coordinate system (the standard x and y) to the polar coordinate system which works 
    # in terms of angles and radius.
    
    horizon_angle = 30
    distance = 100
    distance_increment = 10

    while True:
        # copy the canvas so we can draw on it
        canvas_copy = canvas.copy()

        # find horizon angle
        angle_degrees = horizon_angle + 90

        # convert to radians
        angle_radians = radians(angle_degrees)
        horizon_angle_radians = radians(horizon_angle)
        
        # find the point
        x = distance * cos(angle_radians) + canvas.shape[1]/2
        y = distance * sin(angle_radians) + canvas.shape[0]/2
        x_rounded = int(np.round(x))
        y_rounded = int(np.round(y))
        center = (x_rounded, y_rounded)
        cv2.circle(canvas_copy, center, 10, (0,0,255),2)

        # draw some text
        text = f'angle: {angle_degrees}'
        pos = (20,30)
        cv2.putText(canvas_copy, text, pos, cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(0,255,0),1,cv2.LINE_AA)
        text = f'distance: {distance}'
        pos = (20,60)
        cv2.putText(canvas_copy, text, pos, cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(0,255,0),1,cv2.LINE_AA)

        # get slope
        run = cos(horizon_angle_radians) 
        rise = sin(horizon_angle_radians)
        if x != 0:
            m = rise / run
            b = y - m * x
            pt1, pt2 = find_points(m, b, canvas.shape)
            if pt1:
                try:
                    cv2.line(canvas_copy, pt1, pt2, (255,0,0),2)
                except:
                    print(f'pt1: {pt1}')
                    print(f'pt2: {pt2}')

        # show the result
        cv2.imshow('canvas_copy', canvas_copy)
        key = cv2.waitKey(15)
        if key == ord('q'):
            break
        elif key == ord('w'):
            distance += distance_increment
        elif key == ord('s'):
            distance -= distance_increment
        elif key == ord('a'):
            horizon_angle -= 1
        elif key == ord('d'):
            horizon_angle += 1

    cv2.destroyAllWindows()
 
if __name__ == "__main__":
    main()