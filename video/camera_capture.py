import cv2

from threading import Thread

import time

class CameraCapture:
    def __init__(self, source: int, width: int, height: int):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)

        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)

        # Thread(target=self._start_stream).start()

    def _start_stream(self):
        self.run = True
        while self.run:
            self.cap.grab()

        self.cap.release()

    def read(self):
        return self.cap.read()[1]

    def release(self):
        self.run = False