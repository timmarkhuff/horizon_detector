from tensorflow.keras.models import load_model
import cv2
from crop_and_scale import get_cropping_and_scaling_parameters, crop_and_scale
from find_horizon import find_horizon
from draw_horizon import draw_horizon

def load_and_test_model():
    # globals
    DESIRED_WIDTH = 100
    DESIRED_HEIGHT = 100

    # # load the model
    # print("Loading model...")
    # model = load_model('model_2022.05.18.00.00.00')

    # # get a summary of the model
    # print(model.summary())

    # define the video capture object
    video_path = "videos/upside_down_and_rightside_up.mp4"
    # video_path = 'C:/Users/Owner/Desktop/runway_detector (in progress)/produced_media/arca1.29.2022/2022.01.29.11.52.05.avi'
    cap = cv2.VideoCapture(video_path)

    # get the first frame so we can define some variables based on it
    ret, frame = cap.read()
    if ret:
        # redefine cap so that we start over from frame 0 in the main loop
        cap = cv2.VideoCapture(video_path)
    else:
        print("Could not read video.")
        return 

    # get some parameters for cropping and scaling
    crop_and_scale_parameters = get_cropping_and_scaling_parameters(frame, DESIRED_WIDTH, DESIRED_HEIGHT)
    scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)
    EXCLUSION_THRESH = scaled_and_cropped_frame.shape[1] * .075
    if crop_and_scale_parameters is None:
        return

    # initialize some values related to findng the horizon
    previous_m = None
    previous_b = None
    
    while True:
        ret, frame = cap.read()
        if ret == False:
            break

        # crop and scale the image
        scaled_and_cropped_frame = crop_and_scale(frame, **crop_and_scale_parameters)

        # # normalize frame
        # preprocessed_frame = scaled_and_cropped_frame/255

        # # reshape to the size the model wants
        # preprocessed_frame = preprocessed_frame.reshape(1,100,100,3)

        # # make prediction
        # raw_prediction = model.predict(preprocessed_frame)
        # if raw_prediction[0][0]> raw_prediction[0][1]:
        #     sky_is_up = 0
        # else:
        #     sky_is_up = 1
        
        angle, offset, sky_is_up, variance, m, b = find_horizon(scaled_and_cropped_frame, previous_m, previous_b, EXCLUSION_THRESH)

        # check the variance to determine if this is a good horizon
        previous_m = None
        previous_b = None
        good_horizon = False
        if variance is not None:
            if variance < 2:
                good_horizon = True
                previous_m = m
                previous_b = b
                
        # draw horizon
        frame = draw_horizon(frame, angle, offset, sky_is_up, good_horizon)
        scaled_and_cropped_frame = draw_horizon(scaled_and_cropped_frame, angle, offset, sky_is_up, good_horizon)
        
        cv2.imshow("Original Video", frame)
        cv2.imshow("Scaled and Cropped Video", scaled_and_cropped_frame)

        key = cv2.waitKey(30)

        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    load_and_test_model()
