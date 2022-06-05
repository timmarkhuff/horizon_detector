import pyttsx3
from queue import Queue
from threading import Thread
from time import sleep

class CustomSpeaker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.queue = Queue()
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
                    self.engine.startLoop(False)
                    print(f'Speaking: {text}')
                    self.engine.say(text)
                    self.engine.iterate()
                    self.engine.endLoop()
                    self.isSpeaking = False
        Thread(target=thread).start()

    def release(self):
        self.run = False