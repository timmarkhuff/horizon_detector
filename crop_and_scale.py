import cv2
import numpy as np

def get_cropping_and_scaling_parameters(original_resolution: tuple, new_resolution: int) -> dict:
    """
    original_resolution: resolution of the original, unscaled frame
    new_resolution: desired resolution for performing inferences, genereally much
                    smaller than original_resolution, e.g. (100, 100)
    """
    new_aspect_ratio = new_resolution[0] / new_resolution[1]
    original_aspect_ratio = original_resolution[0] / original_resolution[1]

    if new_aspect_ratio > original_aspect_ratio:
        print(f"Requested aspect ratio of {new_aspect_ratio} is wider than original aspect ratio of {original_aspect_ratio}. "\
                "This is not allowed.")
        new_aspect_ratio = original_aspect_ratio
        print(f'Aspect ratio of {new_aspect_ratio} will be used instead.')

    # define some variables related to cropping
    height = original_resolution[1]
    width = original_resolution[0]
    new_width = height * new_aspect_ratio
    margin = (width - new_width) // 2
    cropping_start = int(margin)
    cropping_end = int(width - margin)
    # define some variables related to scaling
    scale_factor = new_resolution[1] / original_resolution[1]
    # convert to dictionary
    crop_and_scale_parameters = {}
    crop_and_scale_parameters['cropping_start'] = cropping_start
    crop_and_scale_parameters['cropping_end'] = cropping_end
    crop_and_scale_parameters['scale_factor'] = scale_factor

    return crop_and_scale_parameters

def crop_and_scale(frame, cropping_start, cropping_end, scale_factor):
    # crop the image
    frame = frame[:,cropping_start:cropping_end]
    # resize the image
    frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
    return frame

if __name__ == "__main__":
    path = 'training_data/sample_images/sample_horizon_corrected.png'
    input_frame = cv2.imread(path)
    input_frame_resolution = input_frame.shape[1::-1]
    print(input_frame_resolution)
    desired_resolution = (100, 100)
    crop_and_scale_parameters = get_cropping_and_scaling_parameters(input_frame_resolution, desired_resolution)
    output_frame = crop_and_scale(input_frame, **crop_and_scale_parameters)
    cv2.imshow("input_frame",input_frame)
    cv2.imshow("output_frame",output_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows