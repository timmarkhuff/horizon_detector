import cv2
import numpy as np
from datetime import datetime
import os
from math import atan2, cos, sin

class SampleImage:
    def __init__(self, file_path):
        global sample_image_list
        # add self to list
        sample_image_list.append(self)

        # define image
        self.file_path = file_path
        self.file_name = self.file_path.split('/')[-1]
        self.img = cv2.imread(self.file_path)
        desired_display_height = 500
        scale_factor = desired_display_height / self.img.shape[0]
        self.img = cv2.resize(self.img, (0, 0), fx=scale_factor, fy=scale_factor)
        
        # define attributes
        self.pt1 = None
        self.pt2 = None
        self.angle = None
        self.offset = None
        self.labeled = False
        self.deleted = False
    
    def update(self, x, y):
        img_width = self.img.shape[0]
        if self.pt1 is None:
            curr_img_object.pt1 = (x/img_width, y/img_width)
        elif self.pt1 is not None:
            self.pt2 = (x/img_width, y/img_width)

        if self.pt1 is not None and self.pt2 is not None:
            self.angle = atan2((self.pt2[1] - self.pt1[1]), (self.pt2[0] - self.pt1[0]))
            self.offset = 1
            m = (self.pt2[1] - self.pt1[1]) / (self.pt2[0] - self.pt1[0])
            b = self.pt1[1] - m * self.pt1[0]
            self.offset = .5 * m + b
            self.reconstruct_pt1_and_pt2()
            self.labeled = True

    def restore_from_save(self, angle, offset):
        # if there is no data to restore, terminate function early
        if angle == "None" or offset == "None":
            self.labeled = False
            return
        
        # update the angle and offset
        self.angle = float(angle)
        self.offset = float(offset)

        # reconstruct pt1 and pt2
        self.reconstruct_pt1_and_pt2()
        
    def reconstruct_pt1_and_pt2(self):
        """
        Extends pt1 and pt2 to the left and right edges of the
        frame respectively.
        This is done to better draw the horizon line.
        """
        x = cos(self.angle)
        y = sin(self.angle) 
        m = y / x
        b = self.offset - m * .5
        self.pt1 = (0, b)
        self.pt2 = (self.img.shape[0], (m * self.img.shape[0] + b))

    def clear(self):
        self.pt1 = None
        self.pt2 = None
        self.angle = None
        self.offset = None
        self.labeled = False


def click_event(event, x, y, flags, param):
    global curr_img_object, sample_image_list, label_filepath
    left_click = (event == cv2.EVENT_LBUTTONDOWN)
    right_click = (event == cv2.EVENT_RBUTTONDOWN)

    if left_click:
        curr_img_object.update(x,y)
      
    if right_click:
        curr_img_object.clear()

    if curr_img_object.pt1 is not None and curr_img_object.pt2 is not None:
        # save changes
        with open(label_filepath, 'w') as f:
            for img in sample_image_list:
                if img.deleted:
                    pass
                else:
                    f.write(f"{img.file_name},{img.angle},{img.offset}\n")

# define list of SampleImage objects
training_data_dir = "training_data/" + input("Enter name of folder containing training data: ")
items = os.listdir(training_data_dir) 
sample_image_list = []
for item in items:
    if item[-4:] == ".png":
        SampleImage(training_data_dir + '/' + item)

# check if labels.txt exists. If not, create it.
label_filepath = training_data_dir + '/' + "label.txt"
if os.path.exists(label_filepath):
  pass
else:
  with open(label_filepath, 'w') as f:
    pass

# read label.txt
with open(label_filepath, encoding='utf-8-sig') as f:
    lines = f.readlines()

# retrieve saved data from label.txt file
retrieved_saved_data = {}
for line in lines:
  line = line.replace("\n","") # remove line breaks
  split = line.split(",")
  file_name = split[0]
  label1 = split[1]
  label2 = split[2]
  retrieved_saved_data[file_name] = (label1, label2)

# check if there is saved data for each image. If so, update the object. 
for img in sample_image_list:
    if img.file_name in retrieved_saved_data:
        angle = retrieved_saved_data[img.file_name][0]
        offset = retrieved_saved_data[img.file_name][1]
        img.restore_from_save(angle, offset)

# main loop
curr_img_idx = 0
while True:
    curr_img_object = sample_image_list[curr_img_idx]
    curr_img = curr_img_object.img

    # skip deleted images
    while curr_img_object.deleted:
        if curr_img_idx >= len(sample_image_list) - 1:
            curr_img_idx = 0
        else:
            curr_img_idx += 1

        curr_img_object = sample_image_list[curr_img_idx]
        curr_img = curr_img_object.img

    img_to_display = curr_img.copy()
    if curr_img_object.pt1 is not None and curr_img_object.pt2 is not None:
        pt1 = (int(curr_img_object.pt1[0] * curr_img.shape[0]), int(curr_img_object.pt1[1] * curr_img.shape[0]))
        pt2 = (int(curr_img_object.pt2[0] * curr_img.shape[0]), int(curr_img_object.pt2[1] * curr_img.shape[0]))
        cv2.line(img_to_display, pt1, pt2, (0,0,255),2)

    cv2.imshow("Image", img_to_display)
    cv2.setMouseCallback("Image", click_event)
    key = cv2.waitKey(1)

    if key == ord('q'):
        break
    elif key == ord("d"):
        curr_img_idx += 1
    elif key == ord('a'):
        curr_img_idx -= 1
    elif key == ord('x'):
        curr_img_object.deleted = True
        print(f'{curr_img_object.file_name} marked for deletion!')

    # prevent the index from going out of range
    try:
        sample_image_list[curr_img_idx]
    except:
        curr_img_idx = 0

# delete any files that were marked for deletion
for sample_img_object in sample_image_list:
    if sample_img_object.deleted:
        os.remove(sample_img_object.file_path) 
        print(f'{sample_img_object.file_path} deleted.')
    else:
        pass
cv2.destroyAllWindows()