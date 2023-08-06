# standard libraries
import cv2
import os
import shutil
import platform
import numpy as np
import json
from time import sleep
from timeit import default_timer as timer
from itertools import count
from datetime import datetime

# my libraries
from video_classes import CustomVideoCapture, CustomVideoWriter
import global_variables as gv
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
from find_horizon import HorizonDetector
from draw_display import draw_horizon, draw_hud, draw_roi
from disable_wifi_and_bluetooth import disable_wifi_and_bluetooth
from flight_controller import FlightController
from global_variables import settings

def main():
    print('----------STARTING HORIZON DETECTOR----------')

    # load settings from txt
    ret = settings.read()
    if not ret:
        print('Failed to read settings. Terminating program.')
        return
    
    # General Constants
    # the video source, either a webcam (by index) or a video file (by file path)
    SOURCE = settings.get_value('source')
    RESOLUTION = settings.get_value('resolution')
    INFERENCE_RESOLUTION = settings.get_value('inference_resolution')
    FPS = settings.get_value('fps')
    # ACCEPTABLE_VARIANCE is percentage of the image height that is considered an acceptable variance
    # for the find_horizon function.
    ACCEPTABLE_VARIANCE = settings.get_value('acceptable_variance')
    # EXCLUSION_THRESH is the angle above and below the previous horizon beyond which  
    # contour points will be filtered out.
    EXCLUSION_THRESH = settings.get_value('exclusion_thresh')
    FOV = settings.get_value('fov')
    OPERATING_SYSTEM = platform.system()

    # Validate inference_resolution
    # check if the inference resolution is too tall
    if INFERENCE_RESOLUTION[1] > RESOLUTION[1]:
        print(f'Specified inference resolution of {INFERENCE_RESOLUTION} is '\
            f' taller than the resolution of {RESOLUTION}. This is not allowed.')
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

    # global variables
    actual_fps = 0
    if OPERATING_SYSTEM == 'Linux':
        # For performance reasons, default to not rending the HUD when
        # running on Raspberry Pi.
        render_image = False
    else:
        render_image = True

    # functions
    def finish_recording():
        """
        Finishes up the recording and saves the diagnostic data file.
        """
        # pack up values into dictionary
        metadata['datetime'] = dt_string
        metadata['ail_kp'] = settings.get_value('ail_kp')
        metadata['elev_kp'] = settings.get_value('elev_kp')
        metadata['max_deflection'] = settings.get_value('max_deflection')
        metadata['servos_reversed'] = settings.get_value('servos_reversed')
        metadata['fps'] = FPS
        metadata['inference_resolution'] = INFERENCE_RESOLUTION
        metadata['resolution'] = RESOLUTION
        metadata['acceptable_variance'] = ACCEPTABLE_VARIANCE
        metadata['exclusion_thresh'] = EXCLUSION_THRESH
        metadata['fov'] = FOV

        # wait for video_writer to finish recording      
        while video_writer.run:
            sleep(.01) 

        # save the json file
        print('Saving diagnostic data...')
        with open(f'{file_path}/{dt_string}.json', 'w') as convert_file: 
            convert_file.write(json.dumps(datadict))
        print('Diagnostic data saved.')
            
        # check if the thumbdrive is attached
        thumbdrive = '/media/pi/scratch'
        if not os.path.exists(thumbdrive):
            return # do nothing with the thumbdrive
        
        # check if the recordings folder exists on the thumbdrive
        # if not, create it
        dst = f'{thumbdrive}/recordings'
        if not os.path.exists(dst):
            os.makedirs(dst)
        
        # move files to thumbdrive
        src_folder = '/home/pi/horizon_detector/recordings'
        for file in os.listdir(src_folder):
                shutil.copy(f'{src_folder}/{file}', dst)
        
    # paused frame displayed when real-time display is not active
    paused_frame = np.zeros((500, 500, 1), dtype = "uint8")
    cv2.putText(paused_frame, 'Real-time display is paused.',(20,30),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'd' to enable real-time display.",(20,60),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'r' to record.",(20,90),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'q' to quit.",(20,120),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.imshow("Real-time Display", paused_frame)

    # define VideoCapture
    video_capture = CustomVideoCapture(RESOLUTION, SOURCE)

    # start VideoStreamer
    video_capture.start_stream()
    sleep(1)

    # get some parameters for cropping and scaling
    crop_and_scale_parameters = get_cropping_and_scaling_parameters(video_capture.resolution, INFERENCE_RESOLUTION)
    
    # define the HorizonDetector
    horizon_detector = HorizonDetector(EXCLUSION_THRESH, FOV, ACCEPTABLE_VARIANCE, INFERENCE_RESOLUTION)
    
    # initialize some values related to the flight controller
    recording_switch_new_position = None
    autopilot_switch_new_position = None
    ail_stick_val, elev_stick_val, ail_val, elev_val, flt_mode, pitch_trim, ail_trim, elev_trim = (0 for _ in range(8))
    
    # perform some start-up operations specific to the Raspberry Pi
    if OPERATING_SYSTEM == "Linux":
        from switches_and_servos import ServoHandler, TransmitterSwitch, TrimReader
        
        # disable wifi and bluetooth on Raspberry Pi
        wifi_response, bluetooth_response = disable_wifi_and_bluetooth()
        print(f'{wifi_response} {bluetooth_response}')
        
        # create TransmitterSwitch objects
        recording_switch = TransmitterSwitch(26, 2)
        autopilot_switch = TransmitterSwitch(6, 2)
            
        # servo handlers
        ail_handler = ServoHandler(13, 12, FPS, 990, 2013)
        elev_handler = ServoHandler(18, 27, FPS, 990, 2013)
        
        # flight controller
        flt_ctrl = FlightController(ail_handler, elev_handler, FPS)
        
        # pitch trim reader
        pitch_trim_reader = TrimReader(25)
        
    # initialize variables for main loop
    t1 = timer() # for measuring frame rate
    n = 0 # frame number
    while video_capture.run:
        # get a frame from the webcam or video
        frame = video_capture.read_frame()

        # crop and scale the image
        scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)

        # find the horizon
        output = horizon_detector.find_horizon(scaled_and_cropped_frame, diagnostic_mode=render_image)
        roll, pitch, variance, is_good_horizon, _ = output
            
        # run the flight controller
        if OPERATING_SYSTEM == "Linux":
            if pitch is not None:
                adjusted_pitch = pitch + pitch_trim
            else:
                adjusted_pitch = None
            ail_stick_val, elev_stick_val, ail_val, elev_val, ail_trim, elev_trim = flt_ctrl.run(roll, adjusted_pitch, is_good_horizon)
            flt_mode = flt_ctrl.program_id  

        # save the horizon data for diagnostic purposes
        if gv.recording:
            # determine the number of the frame within the current recording
            recording_frame_num = next(recording_frame_iter)

            # save diagnostic data to frame_data dictionary
            frame_data = {}
            frame_data['roll'] = roll
            frame_data['pitch'] = pitch
            frame_data['variance'] = variance
            frame_data['is_good_horizon'] = is_good_horizon
            frame_data['actual_fps'] = actual_fps
            frame_data['ail_val'] = ail_val
            frame_data['elev_val'] = elev_val
            frame_data['ail_stick_val'] = ail_stick_val
            frame_data['elev_stick_val'] = elev_stick_val
            frame_data['ail_trim'] = ail_trim
            frame_data['elev_trim'] = elev_trim
            frame_data['flt_mode'] = flt_mode
            frame_data['pitch_trim'] = pitch_trim 
            frames[recording_frame_num] = frame_data
         
        if render_image:
            frame_copy = frame.copy() # copy the frame so that we have an unmarked frame to draw on
            # draw roi
            draw_roi(frame_copy, crop_and_scale_parameters)
            
            # draw pitch trim
            if roll and is_good_horizon:
                color = (240,240,240)
                adjusted_pitch = pitch + pitch_trim
                draw_horizon(frame_copy, roll, adjusted_pitch, FOV, color, draw_groundline=False)
            
            # draw horizon
            if roll:
                if is_good_horizon:
                    color = (255,0,0)
                else:
                    color = (0,0,255)
                draw_horizon(frame_copy, roll, pitch, 
                            FOV, color, draw_groundline=is_good_horizon)

            # draw HUD
            draw_hud(frame_copy, roll, pitch, actual_fps, is_good_horizon, gv.recording)

            # draw center circle
            center = (frame_copy.shape[1]//2, frame_copy.shape[0]//2)
            radius = frame.shape[0]//100
            cv2.circle(frame_copy, center, radius, (255,0,0), 2)

            # show image
            cv2.imshow("Real-time Display", frame_copy)

        # add frame to recording queue
        if gv.recording:
            video_writer.queue.put(frame)     

        # check for user input
        if OPERATING_SYSTEM == 'Linux':
            autopilot_switch_new_position = autopilot_switch.detect_position_change()
            
        if OPERATING_SYSTEM == 'Linux' and flt_mode != 2:
            recording_switch_new_position = recording_switch.detect_position_change()
        elif OPERATING_SYSTEM == 'Linux' and flt_mode == 2:
            recording_switch_new_position = None
            pitch_trim = pitch_trim_reader.read()
               
        key = cv2.waitKey(1)
        
        # do things based on detected user input
        if key == ord('q'):
            break
        elif key == ord('d'):
            cv2.destroyAllWindows()
            cv2.imshow("Real-time Display", paused_frame)
            render_image = not render_image
            print(f'Real-time display: {render_image}')
        elif autopilot_switch_new_position == 1 and flt_ctrl.program_id != 2:
            flt_ctrl.select_program(2)
        elif autopilot_switch_new_position == 0 and flt_ctrl.program_id == 2:
            flt_ctrl.select_program(0)
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
            file_path = 'recordings'
            video_writer = CustomVideoWriter(filename, file_path, video_capture.resolution, FPS)
            video_writer.start_writing()

            # create some dictionaries to save the diagnostic data
            datadict = {} # top-level dictionary that contains all diagnostic data
            metadata = {} # metadata for the recording (resolution, fps, datetime, etc.)
            frames = {} # contains data for each frame of the recording
            datadict['metadata'] = metadata
            datadict['frames'] = frames
            
            # do a surface check
            if OPERATING_SYSTEM == 'Linux':
                flt_ctrl.select_program(1)
                
        elif (key == ord('r') or recording_switch_new_position == 0) and gv.recording:
            # toggle the recording flag
            gv.recording = not gv.recording
            
            # finish the recording, save diagnostic about recording
            finish_recording()
            
            # wiggle servos to confirm completion of recording
            if OPERATING_SYSTEM == 'Linux':
                flt_ctrl.select_program(3)

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
    if gv.recording:
        gv.recording = not gv.recording
        finish_recording()
    video_capture.release()
    cv2.destroyAllWindows()
    gv.recording = False
    gv.run = False
    print('---------------------END---------------------')

if __name__ == '__main__':
    main()
