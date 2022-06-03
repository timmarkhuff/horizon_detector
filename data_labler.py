import cv2
import os
from math import atan2, cos, sin, pi
from draw_horizon import draw_horizon
from find_horizon import adjust_angle

# settings
view_unlabeled = True
view_labeled = False
view_nondeleted = True
view_deleted = False

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
        if self.pt1 is None:
            self.pt1 = (x, y)
        elif self.pt1 is not None:
            self.pt2 = (x, y)

        if self.pt1 is not None and self.pt2 is not None:
            if self.pt1[0] > self.pt2[0]:
                sky_is_up = False
            else:
                sky_is_up = True

            self.angle = atan2((self.pt2[1] - self.pt1[1]), (self.pt2[0] - self.pt1[0]))
            self.angle = adjust_angle(self.angle, sky_is_up)
            m = (self.pt2[1] - self.pt1[1]) / (self.pt2[0] - self.pt1[0])
            b = self.pt1[1] - m * self.pt1[0]
            self.offset = (m * self.img.shape[1]//2 + b) / self.img.shape[0]
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
        self.labeled = True
        
    def reconstruct_pt1_and_pt2(self):
        """
        Rebuild pt1 and pt2 based on the angle and offset.
        pt1 and pt2 are necessary for drawing the line, but they don't
        exist in label.txt, so they must be reconstructed.
        """
        x = cos(self.angle)
        y = sin(self.angle) 
        m = y / x
        b = self.offset - m * .5

        self.pt1 = (0, b)
        self.pt2 = (self.img.shape[1], (m * self.img.shape[1] + b))

    def clear(self):
        self.pt1 = None
        self.pt2 = None
        self.angle = None
        self.offset = None
        self.labeled = False

    @staticmethod
    def get_next_image(curr_img_idx, increment):
        """
        increment: the amount by which you want to change the image index
        e.g. 1 means next image, -1 means previous image
        """
        global sample_image_list
        global view_unlabeled, view_labeled, view_deleted
        
        # increment the image index
        next_img_index = curr_img_idx + increment

        attempts = 0
        while attempts <= len(sample_image_list):
            # keep the index from going out of bounds
            if next_img_index >= len(sample_image_list):
                next_img_index = 0
            elif next_img_index < 0:
                next_img_index += len(sample_image_list)
            
            # get the next image
            next_img = sample_image_list[next_img_index]
            
            # check if the next image that was grabbed adheres to the settings
            cond1 = (view_unlabeled and next_img.labeled == False)
            cond2 = (view_labeled and next_img.labeled == True)
            cond3 = (view_nondeleted and next_img.deleted == False)
            cond4 = (view_deleted and next_img.deleted == True)

            if (cond1 or cond2) and (cond3 or cond4):
                return next_img_index
            
            # count the attempt
            attempts += 1
            # increment the image index and reattempt
            next_img_index += increment
            
        print("No more images to show given your current settings.")
        return curr_img_idx

def click_event(event, x, y, flags, param):
    global curr_img_object, sample_image_list, label_filepath
    left_click = (event == cv2.EVENT_LBUTTONDOWN)
    right_click = (event == cv2.EVENT_RBUTTONDOWN)

    if left_click:
        curr_img_object.update(x,y)
      
    if right_click:
        curr_img_object.clear()

    if curr_img_object.pt1 is not None and curr_img_object.pt2 is not None:
        save_changes(sample_image_list)

def save_changes(sample_image_list):
    """
    Saves changes to labels.txt
    """
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
label_filepath = training_data_dir + '/' + "labels.txt"
if os.path.exists(label_filepath):
  pass
else:
  with open(label_filepath, 'w') as f:
    pass

# read labels.txt
with open(label_filepath, encoding='utf-8-sig') as f:
    lines = f.readlines()

# retrieve saved data from labels.txt file
retrieved_saved_data = {}
for line in lines:
  line = line.replace("\n","") # remove line breaks
  split = line.split(",")
  file_name = split[0]
  angle = split[1]
  offset = split[2]
  retrieved_saved_data[file_name] = [angle, offset]

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

    img_to_display = curr_img.copy()
    if curr_img_object.pt1 is not None and curr_img_object.pt2 is not None:
        # draw horizon
        angle = curr_img_object.angle
        offset = curr_img_object.offset
        img_to_display = draw_horizon(img_to_display, angle, offset, True)

    # draw "Marked for deletion" text
    if curr_img_object.deleted:
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (50, 50)
        fontScale = 1
        color = (0, 0, 255)
        thickness = 2
        image = cv2.putText(img_to_display, 'Marked for deletion', org, font, 
                        fontScale, color, thickness, cv2.LINE_AA)

    cv2.imshow("Image", img_to_display)
    cv2.setMouseCallback("Image", click_event)
    key = cv2.waitKey(1)

    if key == ord('q'):
        break
    elif key == ord("d"):
        curr_img_idx = curr_img_object.get_next_image(curr_img_idx, 1)
    elif key == ord('a'):
        curr_img_idx = curr_img_object.get_next_image(curr_img_idx, -1)
    elif key == ord('x'):
        curr_img_object.deleted = not curr_img_object.deleted
        print(f'{curr_img_object.file_name} marked for deletion!')
    elif key == ord('1'):
        view_unlabeled = not view_unlabeled
        print(f'view_unlabeled: {view_unlabeled}')
    elif key == ord('2'):
        view_labeled = not view_labeled
        print(f'view_labeled: {view_labeled}')
    elif key == ord('3'):
        view_nondeleted = not view_nondeleted
        print(f'view_nondeleted: {view_nondeleted}')
    elif key == ord('4'):
        view_deleted = not view_deleted
        print(f'view_deleted: {view_deleted}')

# delete any files that were marked for deletion
for sample_img_object in sample_image_list:
    if sample_img_object.deleted:
        os.remove(sample_img_object.file_path) 
        print(f'{sample_img_object.file_path} deleted.')
    else:
        pass

# save changes one more time for good measure
save_changes(sample_image_list)

cv2.destroyAllWindows()