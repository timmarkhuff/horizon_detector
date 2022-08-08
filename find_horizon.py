######## Horizon Detection Using Basic Image Processing #########
# Author: Tim Huff

import cv2
import skimage.measure
import platform
import numpy as np
from numpy.linalg import norm
from math import atan2, cos, sin, pi, degrees, radians
from draw_display import draw_horizon

# constants
FULL_ROTATION = 360
OPERATING_SYSTEM = platform.system()
POOLING_KERNEL_SIZE = 5

class HorizonDetector:
    def __init__(self, exclusion_thresh: float, fov: float, acceptable_variance: float):
        """
        exclusion_thresh: parameter that controls how close horizon points have to be
        to predicted horizon in order to be considered valid
        fov: field of view of the camera
        acceptable_variance: minimum acceptable variance for horizon contour points.
        """
        self.exclusion_thresh = exclusion_thresh
        self.fov = fov
        self.acceptable_variance = acceptable_variance
        self.predicted_roll = None
        self.predicted_pitch = None
        self.recent_horizons = [None, None]

    def find_horizon(self, frame:np.ndarray, diagnostic_mode:bool=False) -> dict:
        """
        frame: the image in which you want to find the horizon
        diagnostic_mode: if True, draws a diagnostic visualization. Should only be used for
        testing, as it slows down performance.
        """
        # default value to return if no horizon can be found
        roll, pitch, variance, is_good_horizon, mask = None, None, None, None, None

        # generate mask
        bgr2gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.bilateralFilter(bgr2gray,9,100,100)
        _, mask = cv2.threshold(blur,250,255,cv2.THRESH_OTSU)
        edges = cv2.Canny(image=blur, threshold1=100, threshold2=200) # (image=blur, threshold1=100, threshold2=200)
        edges = skimage.measure.block_reduce(edges, (POOLING_KERNEL_SIZE , POOLING_KERNEL_SIZE), np.max)

        # find contours
        # chain = cv2.CHAIN_APPROX_SIMPLE
        chain = cv2.CHAIN_APPROX_NONE 
        if OPERATING_SYSTEM == "Linux": # for raspberry pi
            _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, chain) 
        else: # for windows
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, chain)

        if len(contours) == 0:
            # If there are too few contours to find a horizon,
            # return a dictionary of None values.
            self._predict_next_horizon()
            return roll, pitch, variance, is_good_horizon, mask

        # find the contour with the largest area
        largest_contour = sorted(contours, key=cv2.contourArea, reverse=True)[0] 

        # extract x and y values from contour
        x_original = np.array([i[0][0] for i in largest_contour])
        y_original = np.array([i[0][1] for i in largest_contour])

        # Find the average position of the contour points.
        # This will help us determine the direction of the sky.
        avg_x = np.average(x_original)
        avg_y = np.average(y_original)

        # remove points that lie on the edge of the frame
        bool_mask = np.logical_and(x_original > 1, x_original < (frame.shape[1] - 1))
        x_abbr = x_original[bool_mask]
        y_abbr = y_original[bool_mask]
        bool_mask = np.logical_and(y_abbr > 1, y_abbr < (frame.shape[0] - 1))
        x_abbr = x_abbr[bool_mask]
        y_abbr = y_abbr[bool_mask]

        # reduce the number of points to improve performance
        maximum_number_of_points = 80
        step_size = len(x_original)//maximum_number_of_points
        if step_size > 1:
            x_abbr = x_abbr[::step_size]
            y_abbr = y_abbr[::step_size]  

        # define some values for checking distance to previous horizon
        if self.predicted_roll is not None:
            # convert predicted_roll to radians
            predicted_roll_radians = radians(self.predicted_roll)

            # find the distance 
            distance = self.predicted_pitch / self.fov * frame.shape[0]

            # define the line perpendicular to horizon
            angle_perp = predicted_roll_radians + pi / 2
            x_perp = distance * cos(angle_perp) + frame.shape[1]/2
            y_perp = distance * sin(angle_perp) + frame.shape[0]/2

            # convert from roll and pitch of predicted horizon to m and b
            run = cos(predicted_roll_radians)
            rise = sin(predicted_roll_radians) 
            if run != 0:
                predicted_m = rise / run
                predicted_b = y_perp - predicted_m * x_perp            

            # define two points on the line from the previous horizon
            p1 = np.array([0, predicted_b])
            p2 = np.array([frame.shape[1], predicted_m * frame.shape[1] + predicted_b])
            p2_minus_p1 = p2 - p1 

        # Initialize some lists to contain the new (filtered) x and y values.
        x_filtered = []
        y_filtered = []
        # Filter out points that don't lie on an edge.
        for idx, x_point in enumerate(x_abbr):
            y_point = y_abbr[idx]

            # evaluate if the point exists on an edge
            if edges[y_point//POOLING_KERNEL_SIZE][x_point//POOLING_KERNEL_SIZE] == 0:
                continue # do not append the point

            # If there is no predicted horizon, perform no further
            # filtering on this point and accept it as valid.
            if self.predicted_roll is None:
                x_filtered.append(x_point)
                y_filtered.append(y_point)
                continue 

            # If there is a predicted horizon, check if the current point
            # is reasonably close to it.
            p3 = np.array([x_point, y_point])
            distance = norm(np.cross(p2_minus_p1, p1-p3))/norm(p2_minus_p1)
            if distance < self.exclusion_thresh:
                x_filtered.append(x_point)
                y_filtered.append(y_point)

        # convert to numpy array
        x_filtered = np.array(x_filtered)
        y_filtered = np.array(y_filtered)

        # Draw the diagnostic information.
        # Only use for diagnostics, as this slows down inferences. 
        if diagnostic_mode:
            # scale up the diagnostic image to make it easier to see
            desired_height = 500
            scale_factor = desired_height / frame.shape[0]
            desired_width = int(np.round(frame.shape[1] * scale_factor))
            desired_dimensions = (desired_width, desired_height)
            mask = cv2.resize(mask, desired_dimensions)
            # convert the diagnostic image to color
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

            # draw the abbreviated points
            for n, i in enumerate(x_abbr):
                circle_x = int(np.round(i * scale_factor))
                circle_y = int(np.round(y_abbr[n] * scale_factor))
                cv2.circle(mask, (circle_x, circle_y), 5, (0,0,255), -1)
            # draw the filtered points
            for n, i in enumerate(x_filtered):
                circle_x = int(np.round(i * scale_factor))
                circle_y = int(np.round(y_filtered[n] * scale_factor))
                cv2.circle(mask, (circle_x, circle_y), 5, (0,255,0), -1)
            # draw the predicted horizon, if there is one
            if self.predicted_roll:
                draw_horizon(mask, self.predicted_roll, self.predicted_pitch, self.fov, (0,150,255),  False)

            # for testing
            edges = cv2.resize(edges, desired_dimensions)
            _, edges_binary = cv2.threshold(edges,10,255,cv2.THRESH_BINARY)
            cv2.imshow('canny', edges_binary)
                
        # Return None values for horizon, since too few points were found.
        if x_filtered.shape[0] < 10:
            self._predict_next_horizon()
            return roll, pitch, variance, is_good_horizon, mask

        # polyfit
        m, b = np.polyfit(x_filtered, y_filtered, 1)
        roll = atan2(m,1)
        roll = degrees(roll)

        # determine the direction of the sky (above or below)
        if m * avg_x + b > avg_y:
            sky_is_up = 1 # above
        else:
            sky_is_up = 0 # below

        # Get pitch
        # Take the distance from center point of the image to the horizon and find the pitch in degrees
        # based on field of view of the camera and the height of the image.
        # Define two points along horizon.
        p1 = np.array([0, b])
        p2 = np.array([frame.shape[1], m * frame.shape[1] + b])
        # Center of the image
        p3 = np.array([frame.shape[1]//2, frame.shape[0]//2])
        # Find distance to horizon
        distance_to_horizon = norm(np.cross(p2-p1, p1-p3))/norm(p2-p1)
        # Find out if plane is pointing above or below horizon
        if p3[1] < m * frame.shape[1]//2 + b and sky_is_up:
            plane_pointing_up = 1
        elif p3[1] > m *frame.shape[1]//2 + b and sky_is_up == False:
            plane_pointing_up = 1
        else:
            plane_pointing_up = 0
        pitch = distance_to_horizon / frame.shape[0] * self.fov
        if not plane_pointing_up:
            pitch *= -1

        # FIND VARIANCE 
        # This will be treated as a confidence score.
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
        
        # adjust the roll within the range of 0 - 360 degrees
        roll = self._adjust_roll(roll, sky_is_up) 

        # determine if the horizon is acceptable
        if variance < self.acceptable_variance: 
            is_good_horizon = 1
        else:
            is_good_horizon = 0

        # predict the approximate position of the next horizon
        self._predict_next_horizon(roll, pitch, is_good_horizon)

        # return the calculated values for horizon
        return roll, pitch, variance, is_good_horizon, mask
    
    def _adjust_roll(self, roll: float, sky_is_up: bool) -> float:
        """
        Adjusts the roll to be within the range of 0-2*pi.
        Removes negative values and values greater than 2*pi.
        """
        roll = abs(roll % FULL_ROTATION)
        in_sky_is_up_sector = (roll >= FULL_ROTATION * .75  or (roll > 0 and roll <= FULL_ROTATION * .25))
        
        if sky_is_up == in_sky_is_up_sector:
            return roll
        if roll < FULL_ROTATION / 2:
            roll += FULL_ROTATION / 2
        else:
            roll -= FULL_ROTATION / 2
        return roll

    def _predict_next_horizon(self, current_roll=None, current_pitch=None, is_good_horizon=None):
        """
        Based on the positions of recent horizons, predict the approximate
        position of the next horizon.
        Used to filter out noise in the next iteration.
        """
        # if the current horizon is not good, mark it as None
        if not is_good_horizon:
            current_horizon = None
        else:
            current_horizon = (current_roll, current_pitch)

        # update the list of recent horizons
        self.recent_horizons.append(current_horizon)
        del self.recent_horizons[0]
        
        # calculate the positions of the next horizon
        if None in self.recent_horizons:
            self.predicted_roll = None
            self.predicted_pitch = None
        else:
            roll1 = self.recent_horizons[0][0]
            roll2 = self.recent_horizons[1][0]
            roll_delta = roll2 - roll1
            self.predicted_roll =  roll2 + roll_delta

            pitch1 = self.recent_horizons[0][1]
            pitch2 = self.recent_horizons[1][1]
            pitch_delta = pitch2 - pitch1
            self.predicted_pitch = pitch2 + pitch_delta

if __name__ == "__main__":
    import numpy as np
    from timeit import default_timer as timer
    from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale

    ITERATIONS = 1000

    # load the image
    path = r"C:\Users\Owner\Desktop\horizon_detector\images\sun_burst.png"
    frame = cv2.imread(path)

    # define some variables related to cropping and scaling
    INFERENCE_RESOLUTION = (100, 100)
    RESOLUTION = frame.shape[1::-1] # extract the resolution from the frame
    CROP_AND_SCALE_PARAM = get_cropping_and_scaling_parameters(RESOLUTION, INFERENCE_RESOLUTION)
    EXCLUSION_THRESH = 10
    FOV = 48.8
    ACCEPTABLE_VARIANCE = 1.3 

    # define the HorizonDetector
    horizon_detector = HorizonDetector(EXCLUSION_THRESH, FOV, ACCEPTABLE_VARIANCE)

    # find the horizon
    print('Starting perf test...')
    t1 = timer()
    for n in range(ITERATIONS):
        # scale the images down
        frame_small = crop_and_scale(frame, **CROP_AND_SCALE_PARAM)
        output = horizon_detector.find_horizon(frame_small, diagnostic_mode=False)

    t2 = timer()
    elapsed_time = t2 - t1
    fps = np.round(ITERATIONS / elapsed_time, decimals=2)
    print(f'Finished at {fps} FPS.')

    # draw the horizon
    output = horizon_detector.find_horizon(frame_small, diagnostic_mode=True)
    roll, pitch, variance, is_good_horizon, mask = output
    color = (255,0,0)
    draw_horizon(frame, roll, pitch, FOV, color, True)
    print(f'Calculated roll: {roll}')
    print(f'Calculated pitch: {pitch}')

    # draw center circle
    center = (frame.shape[1]//2, frame.shape[0]//2)
    radius = frame.shape[0]//100
    cv2.circle(frame, center, radius, (255,0,0), 2)

    # show results
    cv2.imshow("frame", frame)
    cv2.imshow("mask", mask)
    cv2.waitKey(0)