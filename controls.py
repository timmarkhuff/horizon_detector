import RPi.GPIO as GPIO
from threading import Thread
from time import sleep
from multiprocessing import Process

import global_variables as gv

class ControlHandler:
    def __init__(self, pin_in, pin_out):
        self.run = False
        self.pin_in = pin_in # 17
        self.pin_out = pin_out # 27
        
        # servo in and outs
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_in, GPIO.IN)
        GPIO.setup(self.pin_out, GPIO.OUT)
        sleep(1)
                
    def start(self):
        self.run = True
        self.check_controls()
        
    def check_controls(self):
        def process():
            while gv.run:
                if gv.autopilot:
                    sleep(.01)
                else:
                    input_signal = GPIO.input(self.pin_in)
                    GPIO.output(self.pin_out, input_signal)
                    # sleep(.0000000001)
            GPIO.cleanup()
        Process(target=process).start()

class ControlHandlerThreaded:
    def __init__(self, pin_in, pin_out):
        self.run = False
        self.pin_in = pin_in # 17
        self.pin_out = pin_out # 27
        
        # servo in and outs
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_in, GPIO.IN)
        GPIO.setup(self.pin_out, GPIO.OUT)
        sleep(1)
                
    def start(self):
        self.run = True
        self.check_controls()
        
    def check_controls(self):
        def thread():
            while gv.run:
                if gv.autopilot:
                    sleep(.01)
                else:
                    input_signal = GPIO.input(self.pin_in)
                    GPIO.output(self.pin_out, input_signal)
                    # sleep(.0000000001)
        Thread(target=thread).start()        
        
        
if __name__ == '__main__':
    control_handler = ControlHandler(17, 27)
    control_handler.start()
    print('Starting...')
    sleep(1000)
    gv.run = False
    print('Ending demo')
    
