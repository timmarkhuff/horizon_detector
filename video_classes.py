# standard libraries
import cv2
import os
from queue import Queue
from threading import Thread
from time import sleep
from timeit import default_timer as timer
import global_variables as gv
import platform

# my libraries
from text_to_speech import speaker

class CustomVideoCapture:
    def __init__(self, resolution=None, source=0):
        self.run = False
        self.source = source
        self.fps_list = []

        # determine if we are streaming from a webcam or a video file
        if source.isnumeric():
            self.source = int(source)
            self.using_camera = True
        else:
            self.using_camera = False
            self.queue = Queue(maxsize=100)

        # define the VideoCapture object
        os = platform.system()
        if os == "Linux" or self.using_camera == False:
            self.cap = cv2.VideoCapture(self.source)
        elif self.using_camera == True:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            
        # define the resolution
        if self.using_camera:
            self.resolution = resolution
        else:
            ret, self.frame = self.cap.read() # read the first frame to get the resolution
            self.resolution = self.frame.shape[:2][::-1]
            # redefine the VideoCapture object so that we start over at frame 0
            self.cap = cv2.VideoCapture(self.source) 
        
        self.cap.set(3,self.resolution[0])
        self.cap.set(4,self.resolution[1])

        speaker.add_to_queue(f'resolution: {self.resolution}')

        # fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        # fourcc = cv2.VideoWriter_fourcc(*'h264')
        # fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)

    def get_frames_from_camera(self):
        self.t1 = timer()
        self.number_of_frames = 0
        while self.run:
            ret, self.frame = self.cap.read()
            if ret:
                self.number_of_frames += 1
            else:
                print('Cannot get frames. Ending program.')
                self.run = False
                self.release()

    def get_frames_from_video_file(self):
        while self.run:
            if self.queue.full():
                sleep(1) # wait a bit for the main loop to catch up
                continue # terminate the current iteration of the loop early
            else:
                sleep(.01)
                ret, frame = self.cap.read()
            
            if ret == False:
                print('Cannot get frames. Ending program.')
                self.release()
                break
            else:
                self.queue.put(frame)

    def read_frame(self):
        # if using webcam
        if self.using_camera:
            return self.frame

        # if streaming from a video file
        if self.queue.empty():
            print('No more frames left in the CustomVideoCapture queue.')
            return None
        else:
            frame = self.queue.get()
            return frame         

    def start_stream(self):
        self.run = True
        print(f'using_camera: {self.using_camera}')
        if self.using_camera:
            Thread(target=self.get_frames_from_camera).start()
        else:
            Thread(target=self.get_frames_from_video_file).start()
            
    def set_resolution(self, resolution):
        self.cap.set(3, resolution[0])
        self.cap.set(4, resolution[1])

    def release(self):
        if self.using_camera:
            self.t2 = timer()
            time_elapsed = self.t2 - self.t1
            average_fps = self.number_of_frames / time_elapsed
            print(f'CustomVideoCapture average FPS: {average_fps}')
        self.run = False
        self.cap.release()

class CustomVideoWriter:
    def __init__(self, filename, file_path, resolution=(1280, 720), fps=30):
        self.filename = filename
        self.file_path = file_path
        self.resolution = resolution
        self.fps = fps

        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        self.writer = cv2.VideoWriter(f'{self.file_path}/{self.filename}', fourcc, fps, self.resolution)
        self.queue = Queue()

    def start_writing(self):
        def thread():
            self.run = True
            speaker.add_to_queue(f'Recording in {self.resolution} at {self.fps} FPS.')
            self.time_spent_writing = 0
            self.frames_written = 0
            while gv.recording or not self.queue.empty():
                if self.queue.empty():
                    sleep(.1)
                    continue
                else:
                    t1 = timer()
                    frame = self.queue.get()
                    self.writer.write(frame)
                    t2 = timer()
                    elapsed_time = t2 - t1
                    self.time_spent_writing += elapsed_time
                    self.frames_written += 1
            self.stop()
            speaker.add_to_queue(f"Recording stopped.")
        Thread(target=thread).start()

    def stop(self):
        self.writer.release()
        self.run = False
        fps = self.frames_written / self.time_spent_writing
        print(f'CustomVideoWriter fps: {fps}')



    


