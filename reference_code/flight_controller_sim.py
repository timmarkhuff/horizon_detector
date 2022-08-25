import cv2
import numpy as np
from draw_display import draw_horizon, draw_servos, draw_hud, draw_roi

class Plane:
    def __init__(self, roll, pitch):
        self.roll = roll
        self.pitch = pitch

class PhysicSimulator:
    def __init__(self, plane):
        self.plane = plane

def main():
    while True:
        canvas = np.zeros((500, 1000, 3), dtype = "uint8")
        cv2.imshow('canvas', canvas)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()