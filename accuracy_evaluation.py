import cv2
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os

# Load the video
# video_path = r"F:\horizon_detector\60_acres_09.25.2022\09.24.2022.14.03.34_output.avi" 
# video_path = r"F:\horizon_detector\60_acres_09.25.2022\09.24.2022.14.03.03_output.avi"  
# video_path = r"F:\horizon_detector\60_acres_09.18.2022\09.17.2022.18.20.38_output.avi"
# video_path = r"F:\horizon_detector\60_acres_09.18.2022\09.17.2022.18.20.47_output.avi"
# video_path = r"F:\horizon_detector\60_acres_09.16.2022\09.15.2022.18.19.36_output.avi"
# video_path = r"F:\horizon_detector\60_acres_09.16.2022\09.15.2022.18.21.51_output.avi"
# video_path = r"F:\horizon_detector\60_acres_09.17.2022\09.17.2022.17.25.42_output.avi"
video_path = r"F:\horizon_detector\60_acres_09.17.2022\09.17.2022.17.25.57_output.avi"

labels_path = 'labels.txt'
cap = cv2.VideoCapture(video_path)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_jump = 30
labels = {}
current_frame = 0

def load_labels():
    if os.path.exists(labels_path):
        with open(labels_path, 'r') as file:
            for line in file:
                frame_num, label = line.strip().split(':', 1)
                labels[int(frame_num)] = label

def show_frame():
    global current_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
    ret, frame = cap.read()
    if ret:
        # Add label text if the frame has been labeled
        label = labels.get(current_frame, "")
        cv2.putText(frame, f"Label: {label}", (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {current_frame}", (5, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        display.imgtk = imgtk
        display.configure(image=imgtk)
    else:
        messagebox.showinfo("End of Video", "No more frames in the video.")

def write_labels():
    with open(labels_path, 'w') as file:
        for frame_num, label in sorted(labels.items()):
            file.write(f"{frame_num},{label}\n")

def label_frame(label):
    global current_frame
    labels[current_frame] = label
    write_labels()
    show_frame()

def change_frame(direction):
    global current_frame
    new_frame = current_frame + (frame_jump * direction)
    if 0 <= new_frame < frame_count:
        current_frame = new_frame
        labels.setdefault(current_frame, '')  # Default empty label for new frame
        write_labels()
        show_frame()
    else:
        messagebox.showinfo("End of Video", "You have reached the end or the beginning of the video.")

def on_key_press(event):
    if event.keysym == 'Left':
        change_frame(-1)
    elif event.keysym == 'Right':
        change_frame(1)
    elif event.char == '1':
        label_frame("Correct")
    elif event.char == '2':
        label_frame("Failure")
    elif event.char == '3':
        label_frame("Incorrect")

# Set up Tkinter window
root = Tk()
root.title("Video Frame Labeling")

# Key bindings
root.bind('<Left>', on_key_press)
root.bind('<Right>', on_key_press)
root.bind('1', on_key_press)
root.bind('2', on_key_press)
root.bind('3', on_key_press)

# Create a label in the root window to show the video frames
display = Label(root)
display.grid(row=0, column=0, columnspan=4)

# Create buttons for labeling
Button(root, text="Correct, above confidence (1)", command=lambda: label_frame("Correct")).grid(row=1, column=0)
Button(root, text="Failure (2)", command=lambda: label_frame("Failure")).grid(row=1, column=1)
Button(root, text="Incorrect, above confidence (3)", command=lambda: label_frame("Incorrect")).grid(row=1, column=2)

# Navigation buttons are now controlled by key bindings
Button(root, text="Previous (Left Arrow)", command=lambda: change_frame(-1)).grid(row=2, column=0)
Button(root, text="Next (Right Arrow)", command=lambda: change_frame(1)).grid(row=2, column=1)

# Load existing labels if available
load_labels()

# Show the first frame
show_frame()

# Start the GUI loop
root.mainloop()

# Release the video capture object and destroy all OpenCV windows
cap.release()
cv2.destroyAllWindows()
