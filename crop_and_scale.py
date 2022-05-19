import cv2
import numpy as np
        
def get_cropping_and_scaling_parameters(frame: np.ndarray, desired_width: int, desired_height: int):
    new_aspect_ratio = desired_width / desired_height
    original_aspect_ratio = frame.shape[1] / frame.shape[0]

    if new_aspect_ratio > original_aspect_ratio:
        print(f"Requested aspect ratio of {new_aspect_ratio} is wider than original aspect ratio of {original_aspect_ratio}. "\
                "This is not allowed. Please choose a different desired width and desired height.")
        return None, None, None

    # define some variables related to cropping
    height = frame.shape[0]
    width = frame.shape[1]
    new_width = height * new_aspect_ratio
    margin = (width - new_width) // 2
    cropping_start = int(margin)
    cropping_end = int(width - margin)
    # define some variables related to scaling
    scale_factor = desired_height / frame.shape[0]
    return cropping_start, cropping_end, scale_factor

def crop_and_scale(frame, cropping_start, cropping_end, scale_factor):
    # crop the image
    frame = frame[:,cropping_start:cropping_end]
    # resize the image
    frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
    return frame

if __name__ == "__main__":
    path = 'training_data/sample_images/sample_horizon_corrected.png'
    input_frame = cv2.imread(path)
    cropping_start, cropping_end, scale_factor = get_cropping_and_scaling_parameters(input_frame, 100, 100)
    output_frame = crop_and_scale(input_frame, cropping_start, cropping_end, scale_factor)
    cv2.imshow("input_frame",input_frame)
    cv2.imshow("output_frame",output_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows