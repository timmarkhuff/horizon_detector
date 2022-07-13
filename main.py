# standard libraries
import cv2
import os
import numpy as np
from argparse import ArgumentParser
import json
from time import sleep
from timeit import default_timer as timer
from itertools import count
from datetime import datetime
from math import sqrt

# my libraries
from video_classes import CustomVideoCapture, CustomVideoWriter
import global_variables as gv
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
from find_horizon import find_horizon, get_pitch
from draw_display import draw_horizon, draw_servos, draw_hud, draw_roi
from text_to_speech import speaker
from flight_controller import get_aileron_value, get_elevator_value
from disable_wifi_and_bluetooth import disable_wifi_and_bluetooth

def main():
    print('----------STARTING HORIZON DETECTOR----------')
    # parse arguments
    parser = ArgumentParser()
    help_text = 'The path to the video. For webcam, enter the index of the webcam you want to use, e.g. 0 '
    parser.add_argument('--source', help=help_text, default='0', type=str)     
    help_text = 'Default resolution used when streaming from camera. Not used when streaming from video file. '\
                   'Options include: 640x480, 1280x720 and 1920x1080.'
    parser.add_argument('--res', help=help_text, default='640x480', type=str)
    help_text = 'Resolution of image upon which inferences will be peformed. Smaller size means faster inferences. '\
                    'Cannot be wider than resolution of input image.'
    parser.add_argument('--inf_res', help=help_text, default='100x100', type=str)     
    help_text = 'Maximum FPS at which inferences will be performed. Actual FPS may be lower if inferences are too slow.'
    parser.add_argument('--fps', help=help_text, default='30', type=int)       
    args = parser.parse_args()

    # General Constants
    SOURCE = args.source
    RESOLUTION_STR = args.res
    RESOLUTION = tuple(map(int, RESOLUTION_STR.split('x')))
    INFERENCE_RESOLUTION_STR = args.inf_res
    INFERENCE_RESOLUTION = tuple(map(int, INFERENCE_RESOLUTION_STR.split('x')))
    FPS = args.fps

    # Validate INFERENCE_RESOLUTION
    # check if the inference resolution is too tall
    if INFERENCE_RESOLUTION[1] > RESOLUTION[1]:
        print(f'Specified inference resolution of {INFERENCE_RESOLUTION} is '\
            f' taller than the resolution of {RESOLUTION}. This is not allowed.')
        INFERENCE_RESOLUTION_STR = "100x100" # the recommend inference resolution
        INFERENCE_RESOLUTION = (100, 100) # the recommend inference resolution
        print(f'Inference resolution has been adjusted to the recommended '\
            f'resolution of {INFERENCE_RESOLUTION}.')
    # check if the inference aspect ratio is too wide
    inference_aspect_ratio = INFERENCE_RESOLUTION[0]/INFERENCE_RESOLUTION[1]
    aspect_ratio = RESOLUTION[0]/RESOLUTION[1]
    if inference_aspect_ratio > aspect_ratio:
        print(f'The specified inference aspect ratio of {inference_aspect_ratio} is '\
                f'wider than the aspect ratio of {aspect_ratio}. This is not allowed')
        inference_height = INFERENCE_RESOLUTION[1]
        inference_width = int(np.round(INFERENCE_RESOLUTION[1] * aspect_ratio))
        INFERENCE_RESOLUTION = (inference_width, inference_height)
        print(f'The inference resolution has been adjusted to: {INFERENCE_RESOLUTION}')

    # Field of View Constants
    # FOV constants for Raspberry Pi Camera v2
    # source: https://www.raspberrypi.com/documentation/accessories/camera.html
    FOV_H = 62.2  
    FOV_V = 48.8
    INF_FOV_H = (INFERENCE_RESOLUTION[0] / INFERENCE_RESOLUTION[1]) / (RESOLUTION[0] / RESOLUTION[1]) * FOV_H
    INF_FOV_V = FOV_V
    INF_FOV_DIAG = sqrt(INF_FOV_H ** 2 + INF_FOV_V **2)

    # global variables
    horizon_detection = True
    autopilot = False

    # functions
    def determine_file_path():
        """
        choose where to write the video output and detection data
        """
        # check if there is a thumbdrive that can be used
        supported_thumbdrives = ['Cruzer', 'SAMSUNG USB', '329A-3084']
        for i in supported_thumbdrives:
            file_path = f'/media/pi/{i}'
            if os.path.exists(file_path):
                break
        else:
            file_path = 'recordings'
            
        # check if the folder exists, if not, create it
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            
        return file_path

    def finish_recording():
        """
        Finishes up the recording and saves the diagnostic data file.
        """
        # count the number of high confidence horizons
        high_conf_horizons = 0
        for value in datadict['frames'].values():
            if value['is_good_horizon'] == 1:
                high_conf_horizons += 1
        high_conf_horizon_ratio = high_conf_horizons / len(frames) 

        # record the actual FPS
        actual_fps_lst = []
        for value in datadict['frames'].values():
            actual_fps_lst.append(value['actual_fps'])
        average_actual_fps = np.average(actual_fps_lst)
        print(f'average_actual_fps: {average_actual_fps}')

        # pack up values into dictionary
        metadata['datetime'] = dt_string
        metadata['resolution'] = RESOLUTION_STR
        metadata['inference_resolution'] = INFERENCE_RESOLUTION_STR
        metadata['fps'] = FPS
        metadata['average_actual_fps'] = average_actual_fps
        metadata['total_frames'] = len(frames)
        metadata['high_conf_horizon_ratio'] = high_conf_horizon_ratio 

        # wait for video_writer to finish recording      
        while video_writer.run:
            sleep(.1) 

        # save the json file
        print('Saving diagnostic data...')
        with open(f'{file_path}/{dt_string}.json', 'w') as convert_file: 
            convert_file.write(json.dumps(datadict))
        print('Diagnostic data saved.')

    # define VideoCapture
    video_capture = CustomVideoCapture(RESOLUTION, source=SOURCE)

    # paused frame displayed when real-time display is not active
    paused_frame = np.zeros((500, 500, 1), dtype = "uint8")
    cv2.putText(paused_frame, 'Real-time display is paused.',(20,30),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'd' to enable real-time display.",(20,60),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'r' to record.",(20,90),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'h' to toggle horizon detection.",(20,120),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'a' to toggle autopilot.",(20,150),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'q' to quit.",(20,180),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.imshow("Real-time Display", paused_frame)

    # get some parameters for cropping and scaling
    crop_and_scale_parameters = get_cropping_and_scaling_parameters(video_capture.resolution, INFERENCE_RESOLUTION)
    
    # Define the exclusion threshold in terms of the height of INFERENCE_RESOLUTION.
    # EXCLUSION_THRESH is the distance from the previous horizon beyond which  
    # contour points will be filtered out.
    EXCLUSION_THRESH = INFERENCE_RESOLUTION[0] * .1

    # Keep track of the two most recent horizons
    # to predict the approximate area of the current horizon.
    recent_horizons = [None, None]
    predicted_angle = None
    predicted_offset = None

    # start VideoStreamer
    video_capture.start_stream()
    sleep(1)
    
    # perform some start-up operations specific to the Raspberry Pi
    if gv.os == "Linux":
        # # import package for handling GPIO pins
        # import pigpio
        #from gpiozero import Servo
        #from gpiozero.pins.pigpio import PiGPIOFactory
        from switches_and_servos import TransmitterSwitch, ServoHandler
        
        # disable wifi and bluetooth on Raspberry Pi
        wifi_response, bluetooth_response = disable_wifi_and_bluetooth()
        speaker.add_to_queue(f'{wifi_response} {bluetooth_response}')
        
        # create TransmitterSwitch object
        recording_switch = TransmitterSwitch(13, 2)
        autopilot_switch = TransmitterSwitch(21, 2)
            
        # define aileron servo handler
        input_pin = 27
        output_pin = 17
        aileron_servo_handler = ServoHandler(input_pin, output_pin)
        # define elevator servo handler
        input_pin = 5
        output_pin = 4
        elevator_servo_handler = ServoHandler(input_pin, output_pin)
        sleep(1)
    
    # initialize variables for main loop
    t1 = timer() # for measuring frame rate
    n = 0 # frame number
    while video_capture.run:
        # get a frame from the webcam or video
        frame = video_capture.read_frame()

        if horizon_detection:
            # crop and scale the image
            scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)

            # find the horizon
            horizon = find_horizon(scaled_and_cropped_frame, predicted_angle, predicted_offset, EXCLUSION_THRESH, diagnostic_mode=True)

            # get the pitch
            pitch = get_pitch(horizon['offset_new'], INF_FOV_DIAG)

            # check the variance to determine if this is a good horizon 
            accetable_variance = 1.3 # percentage of the image height that is considered an acceptable variance
            if horizon['variance'] and horizon['variance'] < accetable_variance: 
                is_good_horizon = 1
                recent_horizons = [horizon, recent_horizons[0]]
            else:
                is_good_horizon = 0
                recent_horizons = [None, recent_horizons[0]]

            # predict the next horizon
            if None in recent_horizons:
                predicted_angle = None
                predicted_offset = None
            else: 
                predicted_angle = recent_horizons[0]['angle'] + recent_horizons[0]['angle'] - recent_horizons[1]['angle'] 
                predicted_offset = recent_horizons[0]['offset'] + recent_horizons[0]['offset'] - recent_horizons[1]['offset']

        # determine servo duties
        if autopilot and is_good_horizon:
            aileron_value = get_aileron_value(horizon['angle'])
            elevator_value = get_elevator_value(pitch)
        else:
            aileron_value = None
            elevator_value = None
        
        # actuate the servos
        if gv.os == 'Linux':
            if not autopilot:
                aileron_servo_handler.passthrough()
                elevator_servo_handler.passthrough(reverse=True)
                
            elif autopilot and aileron_value:
                aileron_servo_handler.actuate(aileron_value)
                elevator_servo_handler.actuate(elevator_value)

        # save the horizon data for diagnostic purposes
        if horizon_detection and gv.recording:
            # determine the number of the frame within the current recording
            recording_frame_num = next(recording_frame_iter)

            # save diagnostic data to frame_data dictionary
            frame_data = {}
            frame_data['angle'] = horizon['angle']
            frame_data['offset'] = horizon['offset']
            frame_data['offset_new'] = horizon['offset_new']
            frame_data['pitch'] = pitch
            frame_data['is_good_horizon'] = is_good_horizon
            frame_data['actual_fps'] = actual_fps
            frame_data['aileron_value'] = aileron_value
            frames[recording_frame_num] = frame_data
         
        if gv.render_image:
            frame_copy = frame.copy() # copy the frame so that we have an unmarked frame to draw on
            # draw roi
            draw_roi(frame_copy, crop_and_scale_parameters)
            # draw horizon
            if horizon['angle']:
                angle = horizon['angle']
                offset = horizon['offset']
                offset_new = horizon['offset_new']
                draw_horizon(frame_copy, angle, offset, offset_new, is_good_horizon, INFERENCE_RESOLUTION)
            # draw HUD
            draw_hud(frame_copy, horizon['angle'], pitch, is_good_horizon, gv.recording)
            # draw aileron
            draw_servos(frame_copy, aileron_value)
            # show image
            cv2.imshow("Real-time Display", frame_copy)

        # add frame to recording queue
        if gv.recording:
            video_writer.queue.put(frame)
        
        # CHECK FOR INPUT
        key = cv2.waitKey(1)
        if gv.os == 'Linux':
            recording_switch_new_position = recording_switch.detect_position_change()
            autopilot_switch_new_position = autopilot_switch.detect_position_change()
        else:
            recording_switch_new_position = None
            autopilot_switch_new_position = None
        if key == ord('q'):
            break
        elif key == ord('d'):
            cv2.destroyAllWindows()
            cv2.imshow("Real-time Display", paused_frame)
            gv.render_image = not gv.render_image
            speaker.add_to_queue(f'Real-time display: {gv.render_image}')
        elif key == ord('h'):
            if gv.recording:
                speaker.add_to_queue('Cannot toggle horizon detection while recording.')
            else:
                horizon_detection = not horizon_detection
                speaker.add_to_queue(f'Horizon detection: {horizon_detection}')
        elif (key == ord('a') or autopilot_switch_new_position == 1) and not autopilot:
            autopilot = True
            speaker.add_to_queue(f'Auto-pilot: {autopilot}')
        elif (key == ord('a') or autopilot_switch_new_position == 0) and autopilot:
            autopilot = False
            speaker.add_to_queue(f'Auto-pilot: {autopilot}')
            if gv.os == 'Linux':
                aileron_servo_handler.actuate(0) # return the servo to center position
                elevator_servo_handler.actuate(0) # return the servo to center position
        elif (key == ord('r') or recording_switch_new_position == 1) and not gv.recording:
            # toggle the recording flag
            gv.recording = not gv.recording
            
            # start the recording
            # create an interator to keep track of frame numbers within the recording
            recording_frame_iter = count()

            # get datetime
            now = datetime.now()
            dt_string = now.strftime("%m.%d.%Y.%H.%M.%S")
            filename = f'{dt_string}.avi'

            # start the CustomVideoWriter
            file_path = determine_file_path()
            video_writer = CustomVideoWriter(filename, file_path, video_capture.resolution, FPS)
            video_writer.start_writing()

            # create some dictionaries to save the diagnostic data
            datadict = {} # top-level dictionary that contains all diagnostic data
            metadata = {} # metadata for the recording (resolution, fps, datetime, etc.)
            frames = {} 
            datadict['metadata'] = metadata
            datadict['frames'] = frames
        elif (key == ord('r') or recording_switch_new_position == 0) and gv.recording:
            # toggle the recording flag
            gv.recording = not gv.recording
            
            # finish the recording, save diagnostic about recording
            if horizon_detection:
                finish_recording()

        # DYNAMIC WAIT
        # Figure out how much longer we need to wait in order 
        # for the actual frame rate to be equal to the target frame rate.
        t2 = timer()
        waited_so_far = t2 - t1
        extra = .0000058 * FPS # compensates for some time that is lost each iteration of loop, not sure why, but this improves accuracy
        addl_time_to_wait = 1/FPS - waited_so_far - extra
        if addl_time_to_wait > 0:
            sleep(addl_time_to_wait)

        # record the actual fps
        t_final = timer()
        actual_fps = 1/(t_final - t1)
        t1 = timer()
        
        # increment the frame count for the whole runtime           
        n += 1
    
    # CLEAN UP AND FINISH PROGRAM
    # Stop the recording if it hasn't already been stopped. 
    if gv.recording and horizon_detection:
        gv.recording = not gv.recording
        finish_recording()
    video_capture.release()
    speaker.release()
    cv2.destroyAllWindows()
    gv.recording = False
    gv.run = False
    sleep(1) 
    print('---------------------END---------------------')

if __name__ == '__main__':
    main()