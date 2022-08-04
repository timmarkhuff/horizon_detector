import cv2
import numpy as np

path = r"C:\Users\Owner\Desktop\horizon.png"
horizon = cv2.imread(path)

path = r"C:\Users\Owner\Desktop\edge.png"
edge = cv2.imread(path, cv2.IMREAD_GRAYSCALE)


canvas = np.zeros((horizon.shape[1], horizon.shape[0], 3), dtype = "uint8")
canvas.fill(210)

background = cv2.bitwise_or(canvas,canvas,mask=edge)
out_img = cv2.add(horizon, background)

cv2.imshow('horizon', horizon)
cv2.imshow('edge', edge)
cv2.imshow('background', background)
cv2.imshow('out_img', out_img)
cv2.waitKey(0)
cv2.destroyAllWindows()