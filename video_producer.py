# standard libraries
import cv2
import numpy as np
import os
import json
from timeit import default_timer as timer

# my libraries
from draw_horizon import draw_horizon

def main():
    # check if the folder exists, if not, create it
    recordings_path = "recordings"
    if not os.path.exists(recordings_path):
        os.makedirs(recordings_path)
    
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
        if filename + '.txt' not in items:
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
        with open(f'{recordings_path}/{video_name}.txt') as json_file:
            datadict = json.load(json_file)

        # extract some values from the metadata
        fps = datadict['metadata']['fps']
        resolution = datadict['metadata']['resolution']

        # define video_capture
        source = f'{recordings_path}/{video_name}.{video_extension}'
        cap = cv2.VideoCapture(source)

        # define video_writer
        output_video_path = f'{recordings_path}/{video_name}_output.{video_extension}'
        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, resolution)

        frame_num = 0
        while True:
            ret, frame = cap.read()
            if ret == False:
                break

            # extract the values
            dict_key = str(frame_num)
            angle = datadict[dict_key]['angle']
            offset = datadict[dict_key]['offset']
            good_horizon = datadict[dict_key]['is_good_horizon']

            # draw the horizon
            if angle != 'null':            
                frame = draw_horizon(frame, angle, offset, good_horizon)

            # send the frame to the queue to be recorded
            writer.write(frame)
            
            # show results
            cv2.imshow(output_video_name, frame)

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

if __name__ == "__main__":
    main()