# standard libraries
import cv2
import numpy as np
import os
import json
from timeit import default_timer as timer

# my libraries
from draw_display import draw_horizon, draw_surfaces, draw_hud, draw_roi
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
from find_horizon import HorizonDetector

# constants
BLUE = (255,0,0)

def main(mode=1, output_res=(1280,720)):
    # check if the folder exists, if not, create it
    recordings_path = "recordings"
    if not os.path.exists(recordings_path):
        os.makedirs(recordings_path)
        print('No files were found in the recordings folder. Please try again.')
        return
    
    # define the list of acceptable video file formats
    acceptable_file_extentions = ['avi','mp4']

    # get a list of all videos in folder
    items = os.listdir(recordings_path)

    # check which of the items in the folder is a video that can be produced
    video_list = []
    for item in items:
        # check if this file has an acceptable extension
        file_extension = item.split('.')[-1]
        if file_extension not in acceptable_file_extentions:
            continue
        
        # check if this video has a corresponding txt file
        filename = item.replace(f'.{file_extension}', '')
        if filename + '.json' not in items:
            continue
        
        # check if the video has already been produced
        output_video_name = f'{filename}_output.{file_extension}'
        if output_video_name in items:
            continue
            
        # If none of the conditions above have been met, then
        # the current file is a valid input video that should be produced.
        video_list.append(item)
    
    if not video_list:
        print('No producible videos found.')
        return
    
    for n, video in enumerate(video_list):
        t1 = timer()
        print('----------------------------------------')
        print(f'Starting to produce {output_video_name}...')

        # define video extension and name
        video_extension = video.split('.')[-1]
        video_name = video.replace(f'.{video_extension}', '')

        # Open JSON file
        with open(f'{recordings_path}/{video_name}.json') as json_file:
            datadict = json.load(json_file)

        # extract some values from the metadata
        fps = datadict['metadata']['fps']
        resolution_str = datadict['metadata']['resolution']
        inf_resolution_str = datadict['metadata']['inference_resolution']
        inf_resolution_str = datadict['metadata']['inference_resolution']
        inf_resolution_str = datadict['metadata']['inference_resolution']
        exclusion_thresh = datadict['metadata']['exclusion_thresh']
        acceptable_variance = datadict['metadata']['acceptable_variance']
        fov = datadict['metadata']['fov']
        resolution = tuple(map(int, resolution_str.split('x')))
        inf_resolution = tuple(map(int, inf_resolution_str.split('x')))

        # define video_capture
        source = f'{recordings_path}/{video_name}.{video_extension}'
        cap = cv2.VideoCapture(source)

        # define video_writer
        output_video_path = f'{recordings_path}/{video_name}_output.{video_extension}'
        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, output_res)

        # get some parameters for cropping and scaling
        # in this context, this will be used for draw_roi
        crop_and_scale_parameters = get_cropping_and_scaling_parameters(resolution, inf_resolution)

        # define the HorizonDetector
        horizon_detector = HorizonDetector(exclusion_thresh, fov, acceptable_variance)

        frame_num = 0
        while True:
            ret, frame = cap.read()
            if ret == False:
                break

            # extract the values
            dict_key = str(frame_num)
            roll = datadict['frames'][dict_key]['roll']
            pitch = datadict['frames'][dict_key]['pitch']
            is_good_horizon = datadict['frames'][dict_key]['is_good_horizon']
            actual_fps = datadict['frames'][dict_key]['actual_fps']

            # normal mode (without diagnostic mask)
            if mode == 0:
                # draw_roi
                draw_roi(frame, crop_and_scale_parameters)

                # draw center circle
                x = frame.shape[1]//2
                y = frame.shape[0]//2
                center = (x, y)
                radius = frame.shape[0]//72
                cv2.circle(frame, center, radius, BLUE, 2)

                # draw the horizon
                if roll != 'null':  
                    if is_good_horizon:
                        color = (255,0,0)
                    else:
                        color = (0,0,255)          
                    draw_horizon(frame, roll, pitch, fov, color, draw_groundline=is_good_horizon)

                # draw HUD
                draw_hud(frame, roll, pitch, actual_fps, is_good_horizon)

            # advanced mode (with diagnostic mask)
            elif mode == 1:
                scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)
                output = horizon_detector.find_horizon(scaled_and_cropped_frame, diagnostic_mode=True)
                roll, pitch, variance, is_good_horizon, diagnostic_mask = output

                # draw_roi
                draw_roi(frame, crop_and_scale_parameters)

                # resize the main frame
                desired_height = output_res[1]
                scale_factor = desired_height / frame.shape[0]
                desired_width = int(np.round(frame.shape[1] * scale_factor))
                desired_dimensions = (desired_width, desired_height)
                resized_frame = cv2.resize(frame, desired_dimensions)

                # draw center circle
                x = resized_frame.shape[1]//2
                y = resized_frame.shape[0]//2
                center = (x, y)
                radius = resized_frame.shape[0]//72
                cv2.circle(resized_frame, center, radius, BLUE, 2)

                # draw the horizon
                if roll != 'null':  
                    if is_good_horizon:
                        color = (255,0,0)
                    else:
                        color = (0,0,255)          
                    draw_horizon(resized_frame, roll, pitch, fov, color, draw_groundline=is_good_horizon)

                # resize the diagnostic mask
                desired_width = output_res[0] - resized_frame.shape[1]
                scale_factor = desired_width / diagnostic_mask.shape[1]
                desired_height = int(np.round(diagnostic_mask.shape[0] * scale_factor))
                desired_dimensions = (desired_width, desired_height)
                resized_diagnostic_mask = cv2.resize(diagnostic_mask, desired_dimensions)

                # stats canvas
                width = resized_diagnostic_mask.shape[1]
                height = (output_res[1] - resized_diagnostic_mask.shape[0]) // 2
                stats_canvas = np.zeros((height, width, 3), dtype = "uint8")
                stats_canvas.fill(210)

                # servo visualization canvas
                surface_canvas = stats_canvas.copy()

                # draw border lines
                border_elements = [stats_canvas, resized_diagnostic_mask, surface_canvas]
                for element in border_elements:
                    points = [(0,0),(element.shape[1],0),(element.shape[1],element.shape[0]),(0,element.shape[1])]
                    for idx, pt in enumerate(points):
                        next_idx = idx + 1
                        if next_idx >= len(points):
                            pt2 = points[0]
                        else:
                            pt2 = points[next_idx]
                        cv2.line(element, pt, pt2, BLUE, 3)
                
                # draw control surfaces and other elements of the HUD
                draw_hud(stats_canvas, roll, pitch, actual_fps, is_good_horizon)
                draw_surfaces(surface_canvas, .1, .9, .35, .65, 0, 0, (0,0,255))

                # stack the frames
                stacked = cv2.vconcat([stats_canvas, resized_diagnostic_mask, surface_canvas])
                frame = cv2.hconcat([resized_frame, stacked])

            # send the frame to the queue to be recorded
            writer.write(frame)
            
            # show results
            cv2.imshow(f'Producing {output_video_name}...', frame)

            # check pressed keys 
            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            # increase frame number
            frame_num += 1

        # finishing message
        t2 = timer()
        elapsed_time = t2 - t1 # seconds
        production_time = np.round((elapsed_time / 60), decimals=2) # minutes
        duration = np.round((frame_num / fps / 60), decimals=2) # minutes
        print(f'Finished producing {output_video_name}.')
        print(f'Video duration: {duration} minutes.')
        print(f'Production time: {production_time} minutes.')

        # close resources
        cap.release()
        writer.release()
        cv2.destroyAllWindows()

    # print final message
    print('----------------------------------------')
    print(f"Finished producing {n + 1} videos.")
    print('----------------------------------------')

if __name__ == "__main__":
    main()