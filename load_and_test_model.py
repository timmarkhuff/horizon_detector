from tensorflow.keras.models import load_model
import cv2
import numpy as np
import random
from math import cos, sin

def load_and_test_model():
    # load the model
    print("Loading model...")
    model = load_model('model_2022.05.18.00.00.00')

    # get a summary of the model
    print(model.summary())

    # define the video capture object
    video_path = "videos/upside_down_and_rightside_up.mp4"
    cap = cv2.VideoCapture(video_path)

    # get the first frame so we can define some variables based on it
    ret, frame = cap.read()
    if ret:
        # redefine cap so that we start over from frame 0 in the main loop
        cap = cv2.VideoCapture(video_path)
    else:
        print("Could not read video.")
        return 

    # define some variables related to cropping
    height = frame.shape[0]
    width = frame.shape[1]
    diff = width - height
    start = diff//2
    end = start + height
    frame = frame[:,start:end]
    # define some variables related to scaling
    desired_height = 100 # for image scaling
    scale_factor = desired_height / frame.shape[0]
    frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
    print(f"frame.shape: {frame.shape}")

    # Define some variables relatd to text
    font = cv2.FONT_HERSHEY_SIMPLEX
    org = (50, 50)
    fontScale = 1
    thickness = 2
    
    while True:
        ret, frame = cap.read()
        if ret == False:
            break

        # crop the image
        scaled_and_cropped_frame = frame[:,start:end]
        # resize the image
        scaled_and_cropped_frame = cv2.resize(scaled_and_cropped_frame, (0, 0), fx=scale_factor, fy=scale_factor)

        # normalize frame
        preprocessed_frame = scaled_and_cropped_frame/255

        # reshape to the size the model wants
        preprocessed_frame = preprocessed_frame.reshape(1,100,100,3)

        # make prediction
        raw_prediction = model.predict(preprocessed_frame)
        if raw_prediction[0][0]> raw_prediction[0][1]:
            text = "Upside Down"
            color = (255,0,0)
        else:
            text = "Right Side Up"
            color = (0,255,0)

        frame = cv2.putText(frame, text, org, font, 
                    fontScale, color, thickness, cv2.LINE_AA)

        # draw horizon
        angle = 0
        offset_normalized = .5
        offset = np.round(offset_normalized * frame.shape[0])
        x = cos(angle)
        y = sin(angle) 
        m = y / x
        b = offset - m * .5
        # find the points to be drawn
        p1_x = 0
        p1_y = int(np.round(b)) # round so that we get an integer
        p1 = (p1_x, p1_y)
        p2_x = frame.shape[1]
        p2_y = int(np.round(m * frame.shape[1] + b))
        p2 = (p2_x, p2_y)

        # print(f'pt1 {p1}')
        # print(f'pt2 {p2}')

        frame = cv2.line(frame, p1, p2, (0,0,255), 2)
        
        cv2.imshow("Original Video", frame)
        cv2.imshow("Scaled and Cropped Video", scaled_and_cropped_frame)

        key = cv2.waitKey(1)

        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    load_and_test_model()
