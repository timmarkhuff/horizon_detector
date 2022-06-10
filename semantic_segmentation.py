import cv2 
import numpy as np

points_list = []
drawing: bool = False
path = "images/Vineyard1.jpg"
img = cv2.imread(path)
img_copy = img.copy()

GREEN = (20,240,20)

def click_event(event, x, y, flags, param):
    global points_list, drawing
    left_click = (event == cv2.EVENT_LBUTTONDOWN)
    right_click = (event == cv2.EVENT_RBUTTONDOWN)

    if left_click:
        drawing = not drawing
    if right_click:
        drawing = False
        points_list = []
    if drawing:
        points_list.append([x,y])

while True:
    img_copy = img.copy()
    img_to_show = img.copy()
    if len(points_list) > 3:
        if drawing:
            for n, point in enumerate(points_list[:-1]):
                cv2.line(img_copy, point, points_list[n+1], GREEN, 2)
        else:
            contours = np.array(points_list)
            img_w_poly = cv2.fillPoly(img_copy, pts=[contours], color=GREEN)
            # img_copy = cv2.addWeighted(img_copy,0.4,img_w_poly,0.9,1)
            img_to_show = (img_copy + img_w_poly)//2

    cv2.imshow('img_to_show', img_to_show)
    cv2.setMouseCallback("img_to_show", click_event)

    key = cv2.waitKey(1)

    if key == ord('q'):
        break

cv2.destroyAllWindows()