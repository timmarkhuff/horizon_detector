import cv2
import numpy as np

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
    ail_deflection = int(np.round(ail_val * full_defection))
    elev_offset = ail_offset
    elev_deflection = int(np.round(elev_val * full_defection))

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

    # draw elevator
    pt1x = left + plane_width//2 - hor_stab_width//2 + elev_offset
    pt1y = top + plane_height - hor_stab_height + elev_deflection
    pt1 = (pt1x , pt1y)
    pt2x = right - plane_width//2 + hor_stab_width//2 - elev_offset
    pt2y = top + plane_height - hor_stab_height
    pt2 = (pt2x, pt2y)
    cv2.rectangle(frame, pt1, pt2, surface_color, -1)

    # draw ailerons
    # left
    pt1 = (left + ail_offset, bottom)
    pt2 = (left + ail_offset + ail_width, bottom + ail_deflection)
    cv2.rectangle(frame, pt1, pt2, surface_color, -1)

    # right
    pt1 = (right - ail_offset, bottom)
    pt2 = (right - ail_offset - ail_width, bottom + -1 * ail_deflection)
    cv2.rectangle(frame, pt1, pt2, surface_color, -1)

if __name__ == "__main__":
    canvas = np.zeros((500, 1000, 3), dtype = "uint8")
    canvas.fill(210)
    draw_surfaces(canvas, .6, .95, .75, .9, .5, -.6, (0,0,255))

    cv2.imshow('canvas', canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()