import cv2
import numpy as np
from datetime import datetime
import os
import random

def extract_training_images():
    # globals
    number_of_images = 300
    desired_height = 500 # for image scaling

    # get the datetime for the output file name
    now = datetime.now()
    dt_string = now.strftime("%m.%d.%Y.%H.%M.%S")

    # take a list of videos
    video_list = ["C:/Users/Owner/Desktop/runway_detector (in progress)/produced_media/arca2.20.2022/2022.02.20.07.57.08.avi",
                    "C:/Users/Owner/Desktop/runway_detector (in progress)/produced_media/arca2.20.2022/2022.02.20.07.58.10.avi",
                    "C:/Users/Owner/Desktop/runway_detector (in progress)/produced_media/arca2.20.2022/2022.02.20.07.57.08_upside_down.avi"]

    # check that all video links are valid and can be read
    print("Checking videos...")
    for video in video_list:
        cap = cv2.VideoCapture(video)
        try:
            ret, frame = cap.read()
        except:
            ret = False
        if ret:
            pass
        else:
            print(f'{video} is not a valid path to the video, or the video cannot be read. Please double check.')
            return # end the whole function if any of the videos cannot be read

    print("All videos are valid.")

    # make a folder for the data
    training_data_path = f'training_data/{dt_string}'
    os.mkdir(training_data_path)

    # count the total number of frames in all videos
    print("Counting the number of frames in all videos...")
    total_number_of_frames=0
    for video in video_list:
        cap = cv2.VideoCapture(video)
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
    step_size = total_number_of_frames // number_of_images
    print(f'average_step_size: {step_size}')

    # start looping over the videos and saving images
    n=0
    image_number = 0
    for video in video_list:
        # define the video capture object
        cap = cv2.VideoCapture(video)

        # get the first frame so we can define some variables based on it
        ret, frame = cap.read()
        # define some variables related to cropping
        height = frame.shape[0]
        width = frame.shape[1]
        diff = width - height
        start = diff//2
        end = start + height
        frame = frame[:,start:end]
        # define some variables related to scaling
        scale_factor = desired_height / frame.shape[0]
        frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
        print(f"frame.shape: {frame.shape}")

        # begin saving images
        while True:
            ret, frame = cap.read()

            if ret == False:
                break

            if n % step_size == 0:
                # crop the image
                frame = frame[:,start:end]
                # resize the image
                frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
                cv2.imwrite(f"{training_data_path}/{image_number}.png",frame)
                image_number += 1

            n+=1

    cap.release()
    print(f"Done! {image_number} images extracted.")

if __name__ == "__main__":
    extract_training_images()
