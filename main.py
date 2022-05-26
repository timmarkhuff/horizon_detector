print('----------STARTING HORIZON DETECTOR----------')
import cv2
import numpy as np
from argparse import ArgumentParser
from time import sleep
from timeit import default_timer as timer

# my libraries
from video_classes import CustomVideoCapture, CustomVideoWriter
import global_variables as gv
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
from find_horizon import find_horizon
from draw_horizon import draw_horizon

def main():
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
    parser.add_argument('--fps', help=help_text, default='20', type=int)        
    args = parser.parse_args()

    # globals
    SOURCE = args.source
    RESOLUTION = (int(args.res.split('x')[0]), int(args.res.split('x')[1]))
    INFERENCE_RESOLUTION = (int(args.inf_res.split('x')[0]), int(args.inf_res.split('x')[1]))
    INFERENCE_FPS = args.fps 

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

        # crop and scale the image
        scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)

        # find the horizon
        horizon = find_horizon(scaled_and_cropped_frame, predicted_angle, predicted_offset, EXCLUSION_THRESH, diagnostic_mode=True)
        if horizon is not None:
            angle = horizon['angle'] 
            offset = horizon['offset'] 
            # sky_is_up = horizon['sky_is_up'] 
            variance = horizon['variance'] 

        # check the variance to determine if this is a good horizon 
        if variance < 1.3: # percentage of the image height that is considered an acceptable variance
            good_horizon = True
            recent_horizons = [horizon, recent_horizons[0]]
        else:
            good_horizon = False
            recent_horizons = [None, recent_horizons[0]]

        # predict the next horizon
        if None in recent_horizons:
            predicted_angle = None
            predicted_offset = None
        else: 
            predicted_angle = recent_horizons[0]['angle'] + recent_horizons[0]['angle'] - recent_horizons[1]['angle'] 
            predicted_offset = recent_horizons[0]['offset'] + recent_horizons[0]['offset'] - recent_horizons[1]['offset'] 
        
        # draw horizon
        if gv.render_image and horizon is not None:
            frame_copy = frame.copy()
            frame_copy = draw_horizon(frame_copy, angle, offset, good_horizon)
            cv2.imshow("frame", frame_copy)
            # cv2.imwrite(f'images/{n}.png', frame)

        # add frame to recording queue
        if gv.recording:
            video_writer.queue.put(frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('d'):
            gv.render_image = not gv.render_image
        elif key == ord('r'):
            if gv.recording == False:
                print('---------------------------------------------')
                print('Recording started.')
                video_writer = CustomVideoWriter(video_capture.resolution, INFERENCE_FPS)
                video_writer.start_writing()
                gv.recording = True
            else:
                gv.recording = False
                print('Recording stopped.')
                print('---------------------------------------------')

        # dynamic wait
        # figure out how much longer we need to wait in order 
        # for the actual frame rate to be equal to the target frame rate
        t2 = timer()
        waited_so_far = t2 - t1
        extra = .0005 # compensates for some time that is lost each iteration of loop, not sure why, but this improves accuracy
        addl_time_to_wait = 1/INFERENCE_FPS - waited_so_far - extra
        if addl_time_to_wait > 0:
            sleep(addl_time_to_wait)

        # record the fps
        t_final = timer()
        actual_fps = 1/(t_final - t1)
        t1 = timer()
        fps_list.append(actual_fps)
        n+=1
    
    average_fps = np.mean(fps_list)
    print(f'main loop average fps: {average_fps}')
    video_capture.release()
    cv2.destroyAllWindows()
    gv.recording = False
    gv.run = False
    sleep(2)
    print('---------------------END---------------------')

if __name__ == '__main__':
    main()

