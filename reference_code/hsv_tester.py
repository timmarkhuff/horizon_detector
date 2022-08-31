# (hMin = 90 , sMin = 0, vMin = 0), (hMax = 115 , sMax = 255, vMax = 255)
import cv2
import sys
import numpy as np

def nothing(x):
    pass

# Create a window
cv2.namedWindow('output')

# create trackbars for color change
cv2.createTrackbar('HMin','output',0,179,nothing) # Hue is from 0-179 for Opencv
cv2.createTrackbar('SMin','output',0,255,nothing)
cv2.createTrackbar('VMin','output',0,255,nothing)
cv2.createTrackbar('HMax','output',0,179,nothing)
cv2.createTrackbar('SMax','output',0,255,nothing)
cv2.createTrackbar('VMax','output',0,255,nothing)

# Set default value for MAX HSV trackbars.
cv2.setTrackbarPos('HMax', 'output', 179)
cv2.setTrackbarPos('SMax', 'output', 255)
cv2.setTrackbarPos('VMax', 'output', 255)

# Initialize to check if HSV min/max value changes
hMin = sMin = vMin = hMax = sMax = vMax = 0
phMin = psMin = pvMin = phMax = psMax = pvMax = 0

path = r"C:\Users\Owner\Desktop\horizon_detector\detection_failures\685.png"
img = cv2.imread(path)
bgr2gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
output = img
waitTime = 33

while(1):

    # get current positions of all trackbars
    hMin = cv2.getTrackbarPos('HMin','output')
    sMin = cv2.getTrackbarPos('SMin','output')
    vMin = cv2.getTrackbarPos('VMin','output')

    hMax = cv2.getTrackbarPos('HMax','output')
    sMax = cv2.getTrackbarPos('SMax','output')
    vMax = cv2.getTrackbarPos('VMax','output')

    # Set minimum and max HSV values to display
    lower = np.array([hMin, sMin, vMin])
    upper = np.array([hMax, sMax, vMax])

    # Create HSV Image and threshold into a range.
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    # mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    output = cv2.add(bgr2gray, mask)

    # Print if there is a change in HSV value
    if( (phMin != hMin) | (psMin != sMin) | (pvMin != vMin) | (phMax != hMax) | (psMax != sMax) | (pvMax != vMax) ):
        print(f"lower = np.array([{hMin}, {sMin}, {vMin}]) ")
        print(f"upper = np.array([{hMax}, {sMax}, {vMax}]) ")
        print('---------------')
        phMin = hMin
        psMin = sMin
        pvMin = vMin
        phMax = hMax
        psMax = sMax
        pvMax = vMax

    # Display output image
    cv2.imshow('output', output)
    cv2.imshow('img',img)

    # Wait longer to prevent freeze for videos.
    if cv2.waitKey(waitTime) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()


# import cv2
# import numpy as np
# # path = r"C:\Users\Owner\Desktop\horizon_detector\detection_failures\2761.png"
# path = r"C:\Users\Owner\Desktop\horizon_detector\detection_failures\doctored_horizon.png"

# frame = cv2.imread(path)

# # scale up the diagnostic image to make it easier to see
# # desired_height = 100
# # scale_factor = desired_height / frame.shape[0]
# # desired_width = int(np.round(frame.shape[1] * scale_factor))
# # desired_dimensions = (desired_width, desired_height)
# # frame = cv2.resize(frame, desired_dimensions)

# bgr2gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# _, mask = cv2.threshold(bgr2gray,250,255,cv2.THRESH_OTSU)

# frame_cropped = frame[:][:]
# bgr2gray_cropped = cv2.cvtColor(frame_cropped, cv2.COLOR_BGR2GRAY)
# _, mask_cropped = cv2.threshold(bgr2gray_cropped,250,255,cv2.THRESH_OTSU)

# cv2.imshow('img', frame)
# cv2.imshow('mask', mask)
# cv2.imshow('frame_cropped', frame_cropped)
# cv2.imshow('mask_cropped', mask_cropped)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
