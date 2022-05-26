import cv2
import numpy as np
from datetime import datetime
import os

from pkg_resources import ResolutionError
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale

def extract_training_images():
    # globals
    NUMBER_OF_IMAGES = 20
    INFERENCE_RESOLUTION = (100, 100)# for image scaling

    # take a list of videos
    folder_path = "C:/Users/Owner/Desktop/runway_detector_in_progress/produced_media/arca2.20.2022/"
    video_list = ["2022.02.20.07.57.08.avi",
                "2022.02.20.07.58.10.avi",
                "2022.02.20.07.57.08_upside_down.avi"]

    # check that all video links are valid and can be read
    print("Checking videos...")
    for video_name in video_list:
        video_path = folder_path + video_name
        cap = cv2.VideoCapture(video_path)

        # check if a frame can be read
        try:
            ret, frame = cap.read()
            resolution = frame.shape[:2][::-1]
        except:
            ret = False
        if ret:
            pass
        else:
            print(f'{video_path} is not a valid path to the video, or the video cannot be read. Please double check.')
            return # end the whole function if any of the videos cannot be read

        # check desired width and desired height
        crop_and_scale_parameters = get_cropping_and_scaling_parameters(resolution, INFERENCE_RESOLUTION)
        if crop_and_scale_parameters is None:
            # if the desired width and height are invalid and an 
            # aspect ratio cannot be returned, terminate function early
            return

    print("All videos are valid.")

    # count the total number of frames in all videos
    print("Counting the number of frames in all videos...")
    total_number_of_frames=0
    for video_path in video_list:
        video_path = folder_path + video_name
        cap = cv2.VideoCapture(video_path)
        while True:
            ret, frame = cap.read()
            if ret:
                total_number_of_frames+=1
            else:
                break

    # report the total number of frames counted
    print(f'total_number_of_frames: {total_number_of_frames}')

    # we will take every nth frame from the videos to yield a certain number of images
    # for this, we will define average_step_size
    step_size = total_number_of_frames // NUMBER_OF_IMAGES
    print(f'step_size: {step_size}')

    # make a folder for the data
    now = datetime.now()
    dt_string = now.strftime("%m.%d.%Y.%H.%M.%S")
    training_data_path = f'training_data/{dt_string}'
    os.mkdir(training_data_path)
    print(f'New folder {training_data_path} created.')

    # start looping over the videos and saving images
    n = 0 # an overall counter for each frame across all videos
    frame_count = 0 # used to count the total number of frames extracted
    for video_name in video_list:
        frame_number = 0 # frame number within this specific video
        video_path = folder_path + video_name
        video_file_basename = '.'.join(video_name.split(".")[:-1])
        # define the video capture object
        cap = cv2.VideoCapture(video_path)
        # get the first frame so we can define some variables based on it
        ret, frame = cap.read()
        # define some variables related to cropping
        crop_and_scale_parameters = get_cropping_and_scaling_parameters(resolution, INFERENCE_RESOLUTION)

        # begin saving images
        while True:
            ret, frame = cap.read()

            if ret == False:
                break

            if n % step_size == 0:
                frame = crop_and_scale(frame, **crop_and_scale_parameters)
                cv2.imwrite(f"{training_data_path}/{video_file_basename}_{frame_number}.png",frame)
                frame_count += 1
            
            frame_number += 1
            n += 1

    cap.release()
    print(f"Done! {frame_count} images extracted.")

if __name__ == "__main__":
    extract_training_images()
