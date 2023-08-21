import cv2
import numpy as np

from queue import Queue
import time
from threading import Thread

class VideoRecorder:
    def __init__(self, file_path: str, width: int, height: int, fps: int) -> None:
        self.sleep_time = 1 / fps

        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        self.writer = cv2.VideoWriter(file_path, fourcc, fps, (width, height))

        self.queue = Queue()

        self._start()

    def _process_queue(self) -> None:
        while self.run or not self.queue.qsize() == 0:
            if self.queue.qsize() == 0:
                time.sleep(self.sleep_time)
                continue
            else:
                frame = self.queue.get()
                self.writer.write(frame)
        self.writer.release()

    def _start(self) -> None:
        self.run = True
        Thread(target=self._process_queue).start()

    def put_in_queue(self, frame: np.ndarray) -> None:
        self.queue.put(frame)

    def release(self):
        self.run = False