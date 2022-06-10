import cv2
import numpy as np

# read the image
filepath = 'dress.png'
img = cv2.imread(filepath)

# find the mask
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# set some absolute values for the threshold, since we know the background will always be white
_, mask = cv2.threshold(img_gray,244,255,cv2.THRESH_BINARY)
mask_inv = cv2.bitwise_not(mask)

# find the largest contour 
contours, _ = cv2.findContours(mask_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
largest_contour = sorted(contours, key=cv2.contourArea, reverse=True)[0]

# draw the largest contour to fill in the holes in the mask
final_result = np.ones(img.shape[:2]) # create a blank canvas to draw the final result
final_result = cv2.drawContours(final_result, [largest_contour], -1, color=(0, 255, 0), thickness=cv2.FILLED)

# show results
cv2.imshow('mask', mask)
cv2.imshow('img', img)
cv2.imshow('final_result', final_result)
cv2.waitKey(0)
cv2.destroyAllWindows()