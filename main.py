import cv2
import numpy as np
from argparse import ArgumentParser
import json
from time import sleep
from timeit import default_timer as timer
from itertools import count
from datetime import datetime

# my libraries
from video_classes import CustomVideoCapture, CustomVideoWriter
import global_variables as gv
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
from find_horizon import find_horizon
from draw_display import draw_horizon, draw_servos, draw_hud
from text_to_speech import speaker
from servos import get_aileron_value

def main():
    print('----------STARTING HORIZON DETECTOR----------')
    # parse arguments
    parser = ArgumentParser()
    help_text = 'The path to the video. For webcam, enter the index of the webcam you want to use, e.g. 0 '
    parser.add_argument('--source', help=help_text, default='0', type=str)     
    help_text = 'Default resolution used when streaming from camera. Not used when streaming from video file. '\
                   'Options include: 640x480, 1280x720 and 1920x1080.'
    parser.add_argument('--res', help=help_text, default='1280x720', type=str)
    help_text = 'Resolution of image upon which inferences will be peformed. Smaller size means faster inferences. '\
                    'Cannot be wider than resolution of input image.'
    parser.add_argument('--inf_res', help=help_text, default='100x100', type=str)     
    help_text = 'Maximum FPS at which inferences will be performed. Actual FPS may be lower if inferences are too slow.'
    parser.add_argument('--fps', help=help_text, default='20', type=int)       

    args = parser.parse_args()

    # globals
    SOURCE = args.source
    RESOLUTION_STR = args.res
    RESOLUTION = tuple(map(int, RESOLUTION_STR.split('x')))
    INFERENCE_RESOLUTION = (int(args.inf_res.split('x')[0]), int(args.inf_res.split('x')[1]))
    FPS = args.fps 
    actual_fps = 0
    horizon_detection = True
    auto_pilot = False

    # functions
    def finish_recording():
        """
        Finishes up the recording and saves the diagnostic data file
        """

        metadata['fps'] = FPS
        metadata['datetime'] = dt_string
        metadata['total_frames'] = next(recording_frame_iter)
        metadata['resolution'] = RESOLUTION_STR
        datadict['metadata'] = metadata
        datadict['frames'] = frames
        # count the number of high confidence horizons
        high_conf_horizon_ratio = 0
        for value in datadict['frames'].values():
            if value['is_good_horizon'] == 1:
                high_conf_horizon_ratio += 1
        metadata['high_conf_horizon_ratio'] = high_conf_horizon_ratio / metadata['total_frames']   

        # wait for video_writer to finish recording      
        while video_writer.run:
            sleep(.1) 

        # save the json file
        with open(f'recordings/{dt_string}.txt', 'w') as convert_file: 
            convert_file.write(json.dumps(datadict))

        # wait for video_writer to finish recording      
        while video_writer.run:
            sleep(.1) 

        # save the json file
        with open(f'recordings/{dt_string}.txt', 'w') as convert_file: 
            convert_file.write(json.dumps(datadict))

    # define VideoCapture
    video_capture = CustomVideoCapture(RESOLUTION, source=SOURCE)

    # paused frame
    paused_frame = np.zeros((500, 500, 1), dtype = "uint8")
    cv2.putText(paused_frame, 'Real-time display is paused.',(20,30),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'd' to enable real-time display.",(20,60),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(paused_frame, "Press 'q' to quit.",(20,90),cv2.FONT_HERSHEY_COMPLEX_SMALL,.75,(255,255,255),1,cv2.LINE_AA)
    cv2.imshow("Real-time Display", paused_frame)

    # get some parameters for cropping and scaling
    crop_and_scale_parameters = get_cropping_and_scaling_parameters(video_capture.resolution, INFERENCE_RESOLUTION)
    EXCLUSION_THRESH = video_capture.resolution[1] * .04
    if not crop_and_scale_parameters:
        print('Could not get cropping and scaling parameters.')
        return

    # keep track of the two most recent horizons
    # used to predict the approximate area of the current horizon
    recent_horizons = [None, None]
    predicted_angle = None
    predicted_offset = None

    # initialize some dictionaries to save the diagnostic data
    datadict = {}
    metadata = {}
    frame_data = {}

    # start VideoStreamer
    video_capture.start_stream()
    sleep(1)
    
    # define servos
    aileron_value = 0
    if gv.os == "Linux":
        from gpiozero import Servo
        from gpiozero.pins.pigpio import PiGPIOFactory
        factory = PiGPIOFactory()
        servo = Servo(17, pin_factory=factory)
        servo.value = 0
        sleep(2)

    # initialize variables for main loop
    fps_list = [] # for measuring frame rate
    t1 = timer() # for measuring frame rate
    n = 0 # frame number
    while video_capture.run:
        # get a frame from the webcam or video
        frame = video_capture.read_frame()

        # initialize a dictionary to contain data about the current frame
        frame_data = {}

        # Initialize the horizon as a dictionary of None values.
        horizon = {}
        horizon['angle'] = None
        horizon['offset'] = None
        horizon['variance'] = None
        horizon['m'] = None
        horizon['b'] = None
        if horizon_detection:
            # crop and scale the image
            scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)

            # find the horizon
            horizon = find_horizon(scaled_and_cropped_frame, predicted_angle, predicted_offset, EXCLUSION_THRESH, diagnostic_mode=True)

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
        if auto_pilot and is_good_horizon:
            aileron_value = get_aileron_value(horizon['angle'])
        else:
            aileron_value = None
        
        # actuate the servos
        if auto_pilot and gv.os == "Linux" and aileron_value: 
            servo.value = aileron_value          

        # save the horizon data for diagnostic purposes
        if horizon_detection and gv.recording:
            # determine the number of the frame within the current recording
            recording_frame_num = next(recording_frame_iter)

            # save horizon data to dictionary
            frame_data = {}
            frame_data['angle'] = horizon['angle']
            frame_data['offset'] = horizon['offset']
            frame_data['is_good_horizon'] = is_good_horizon
            frame_data['fps'] = actual_fps
            frame_data['aileron_value'] = aileron_value
            frames[recording_frame_num] = frame_data
         
        if gv.render_image:
            frame_copy = frame.copy()
            # draw horizon
            if horizon['angle'] and gv.render_image:
                frame_copy = draw_horizon(frame_copy, horizon['angle'], horizon['offset'], is_good_horizon)
            # draw HUD
            draw_hud(frame_copy, horizon['angle'], horizon['offset'], is_good_horizon, gv.recording)
            # draw aileron
            frame_copy = draw_servos(frame_copy, aileron_value)
            # show image
            cv2.imshow("Real-time Display", frame_copy)

        # add frame to recording queue
        if gv.recording:
            video_writer.queue.put(frame)

        # wait and check for pressed keys
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('d'):
            cv2.imshow("Real-time Display", paused_frame)
            gv.render_image = not gv.render_image
            speaker.add_to_queue(f'Real-time display: {gv.render_image}')
        elif key == ord('h'):
            if gv.recording:
                speaker.add_to_queue('Cannot toggle horizon detection while recording.')
            else:
                horizon_detection = not horizon_detection
                speaker.add_to_queue(f'Horizon detection: {horizon_detection}')
        elif key == ord('a'):
            if horizon_detection:
                auto_pilot = not auto_pilot
                speaker.add_to_queue(f'Auto-pilot: {auto_pilot}')
            else:
                speaker.add_to_queue('Cannot enable autopilot without horizon detection.')
        elif key == ord('r'):
            gv.recording = not gv.recording
            if gv.recording:
                # create an interator to keep track of frame numbers
                recording_frame_iter = count()

                # get datetime
                now = datetime.now()
                dt_string = now.strftime("%m.%d.%Y.%H.%M.%S")
                filename = f'{dt_string}.avi'

                # start the CustomVideoWriter
                video_writer = CustomVideoWriter(filename, video_capture.resolution, FPS)
                video_writer.start_writing()

                # create some dictionaries to save the diagnostic data
                datadict = {}
                metadata = {}
                frames = {}
                frame_data = {}
            else:
                # save diagnostic about recording
                if horizon_detection:
                    finish_recording()

        # DYNAMIC WAIT
        # Figure out how much longer we need to wait in order 
        # for the actual frame rate to be equal to the target frame rate.
        t2 = timer()
        waited_so_far = t2 - t1
        extra = .0005 # compensates for some time that is lost each iteration of loop, not sure why, but this improves accuracy
        addl_time_to_wait = 1/FPS - waited_so_far - extra
        if addl_time_to_wait > 0:
            sleep(addl_time_to_wait)

        # record the actual fps
        t_final = timer()
        actual_fps = 1/(t_final - t1)
        t1 = timer()
        fps_list.append(actual_fps) # for measuring the fps of the entire runtime
        
        # increment the frame count for the whole runtime           
        n += 1
    
    # CLEAN UP AND FINISH PROGRAM
    # Stop the recording if it hasn't already been stopped. 
    if gv.recording and horizon_detection:
        gv.recording = not gv.recording
        finish_recording()
    average_fps = np.mean(fps_list)
    print(f'main loop average fps: {average_fps}')
    video_capture.release()
    speaker.release()
    cv2.destroyAllWindows()
    gv.recording = False
    gv.run = False
    
    # clean up servos
    if gv.os == "Linux":
        servo.value = 0
        
    sleep(1)
    
    print('---------------------END---------------------')

if __name__ == '__main__':
    main()