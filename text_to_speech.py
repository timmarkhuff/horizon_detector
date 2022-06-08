import pyttsx3
from queue import Queue
from threading import Thread
from time import sleep

class CustomSpeaker:
    def __init__(self, q_maxsize=3):
        self.q_maxsize = q_maxsize
        self.engine = pyttsx3.init()
        self.queue = Queue(maxsize=self.q_maxsize)
        self.isSpeaking = False
        self.run = True
        self.start()

    def start(self):
        def thread():
            while self.run:
                if self.queue.empty():
                    sleep(.01)
                else:
                    self.isSpeaking = True
                    text = self.queue.get()
                    print(f'Speaking: {text}')
                    self.engine.startLoop(False)
                    self.engine.say(text)
                    self.engine.iterate()
                    self.engine.endLoop()
                    self.isSpeaking = False
        Thread(target=thread).start()

    def release(self):
        self.run = False

    def add_to_queue(self, text):
        if self.queue.full():
            print(f'Text-to-speech queue is full, maxsize: {self.q_maxsize}')
            print('Cannot add any more items.')
        else:
            self.queue.put(text)

# define the custom speaker
speaker = CustomSpeaker()
