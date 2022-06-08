print('----------STARTING HORIZON DETECTOR----------')
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
from draw_horizon import draw_horizon
from text_to_speech import speaker

def main():
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
    RESOLUTION = (int(args.res.split('x')[0]), int(args.res.split('x')[1]))
    INFERENCE_RESOLUTION = (int(args.inf_res.split('x')[0]), int(args.inf_res.split('x')[1]))
    FPS = args.fps 
    horizon_detection_on = False

    # define VideoCapture
    video_capture = CustomVideoCapture(RESOLUTION, source=SOURCE)

    # get some parameters for cropping and scaling
    crop_and_scale_parameters = get_cropping_and_scaling_parameters(video_capture.resolution, INFERENCE_RESOLUTION)
    EXCLUSION_THRESH = video_capture.resolution[1] * .04
    if crop_and_scale_parameters is None:
        print('Could not get cropping and scaling parameters.')
        return

    # keep track of the two most recent horizons
    # used to predict the approximate area of the current horizon
    recent_horizons = [None, None]
    predicted_angle = None
    predicted_offset = None

    # start VideoStreamer
    video_capture.start_stream()
    sleep(1)

    # initialize variables for main loop
    fps_list = []# for measuring frame rate
    t1 = timer() # for measuring frame rate
    n = 0 # frame number
    while video_capture.run:
        # get a frame
        frame = video_capture.read_frame()
        frame_copy = frame.copy()

        horizon = None # initialize the value
        if horizon_detection_on:
            # crop and scale the image
            scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)

            # find the horizon
            horizon = find_horizon(scaled_and_cropped_frame, predicted_angle, predicted_offset, EXCLUSION_THRESH, diagnostic_mode=True)
            if horizon is not None:
                angle = horizon['angle'] 
                offset = horizon['offset'] 
                variance = horizon['variance'] 

            # check the variance to determine if this is a good horizon 
            if variance < 1.3: # percentage of the image height that is considered an acceptable variance
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
            
        if horizon_detection_on and gv.recording:
            # determine the number of the frame within the current recording
            recording_frame_num = next(recording_frame_iter)

            # save horizon data to dictionary
            frame_data = {}
            if horizon is not None:
                frame_data['angle'] = horizon['angle']
                frame_data['offset'] = horizon['offset']
                frame_data['is_good_horizon'] = is_good_horizon
            else:
                frame_data['angle'] = None
                frame_data['offset'] = None
                frame_data['is_good_horizon'] = None

            datadict[recording_frame_num] = frame_data
            
        # draw horizon
        if horizon is not None and gv.render_image:
            frame_copy = draw_horizon(frame_copy, angle, offset, is_good_horizon)
            # cv2.imwrite(f'images/{n}.png', frame) # save individual frames for diagnostics

        # show image
        if gv.render_image:
            cv2.imshow("frame", frame_copy)
            # cv2.imwrite(f'images/{n}.png', frame) # save individual frames for diagnostics

        # add frame to recording queue
        if gv.recording:
            video_writer.queue.put(frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('d'):
            gv.render_image = not gv.render_image
        elif key == ord('h'):
            horizon_detection_on = not horizon_detection_on
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
            else:
                # save diagnostic about recording
                if horizon_detection_on:
                    # save metadata about recording
                    metadata['fps'] = FPS
                    metadata['datetime'] = dt_string
                    metadata['total_frames'] = next(recording_frame_iter)
                    metadata['resolution'] = RESOLUTION
                    datadict['metadata'] = metadata

                    # wait for video_writer to finish recording      
                    while video_writer.run:
                        sleep(.1) 

                    # save the json file
                    with open(f'recordings/{dt_string}.txt', 'w') as convert_file: 
                        convert_file.write(json.dumps(datadict))

        # DYNAMIC WAIT
        # Figure out how much longer we need to wait in order 
        # for the actual frame rate to be equal to the target frame rate.
        t2 = timer()
        waited_so_far = t2 - t1
        extra = .0005 # compensates for some time that is lost each iteration of loop, not sure why, but this improves accuracy
        addl_time_to_wait = 1/FPS - waited_so_far - extra
        if addl_time_to_wait > 0:
            sleep(addl_time_to_wait)

        # record the fps
        t_final = timer()
        actual_fps = 1/(t_final - t1)
        t1 = timer()
        fps_list.append(actual_fps) # for measuring the fps of the entire runtime
        n += 1
    
    average_fps = np.mean(fps_list)
    print(f'main loop average fps: {average_fps}')
    video_capture.release()
    speaker.release()
    cv2.destroyAllWindows()
    gv.recording = False
    gv.run = False
    sleep(1)
    print('---------------------END---------------------')

if __name__ == '__main__':
    main()