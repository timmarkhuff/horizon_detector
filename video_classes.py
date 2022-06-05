import cv2
import numpy as np
from queue import Queue
from threading import Thread
from time import sleep
from timeit import default_timer as timer
import global_variables as gv
from datetime import datetime
import platform

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
            self.queue = Queue(maxsize=1000)

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

        print(f'resolution: {self.resolution}')

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    def get_frames_from_webcam(self):
        t1 = timer()
        while self.run:
            ret, self.frame = self.cap.read()
            t2 = timer()
            fps = 1 / (t2 - t1)
            t1 = timer()
            self.fps_list.append(fps)
            if ret == False:
                print('Cannot get frames. Ending program.')
                self.run = False
                self.release()

    def get_frames_from_video_file(self):
        while self.run:
            t1 = timer()
            if self.queue.full():
                sleep(1) # wait a bit for the main loop to catch up
                continue # terminate the current iteration of the loop early
                
            else:
                ret, frame = self.cap.read()
            
            if ret == False:
                print('Cannot get frames. Ending program.')
                self.release()
                break
            else:
                self.queue.put(frame)
            t2 = timer()
            fps = 1 / (t2 - t1)
            self.fps_list.append(fps)


    def read_frame(self):
        # if using webcam
        if self.using_camera:
            return self.frame

        # if streaming from a video file
        if self.queue.empty():
            self.run = False
            print('No more frames left in the queue.')
            self.release()
        else:
            frame = self.queue.get()
            return frame         

    def start_stream(self):
        self.run = True
        print(f'using_camera: {self.using_camera}')
        if self.using_camera:
            Thread(target=self.get_frames_from_webcam).start()
        else:
            Thread(target=self.get_frames_from_video_file).start()
            
    def set_resolution(self, resolution):
        self.cap.set(3, resolution[0])
        self.cap.set(4, resolution[1])

    def release(self):
        average_fps = np.average(self.fps_list)
        print(f'CustomVideoCapture average FPS: {average_fps}')
        self.run = False
        self.cap.release()

class CustomVideoWriter:
    def __init__(self, resolution=(1280, 720), fps=30):
        self.resolution = resolution
        self.fps = fps
        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        now = datetime.now()
        self.dt_string = now.strftime("%m.%d.%Y.%H.%M.%S")
        self.writer = cv2.VideoWriter(f'recordings/{self.dt_string}.avi', fourcc, fps, self.resolution)
        self.queue = Queue()

    def start_writing(self):
        def thread():
            print(f'Recording in {self.resolution} at {self.fps} FPS.')
            while gv.recording or not self.queue.empty():
                if self.queue.empty():
                    sleep(1)
                    continue
                else:
                    frame = self.queue.get()
                    self.writer.write(frame)
            self.stop()
            print(f"Finished writing video {self.dt_string}.avi.")
        Thread(target=thread).start()

    def stop(self):
        self.writer.release()


    


