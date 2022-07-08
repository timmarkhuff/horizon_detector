from gpiozero import Servo
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory
from threading import Thread
from multiprocessing import Process
import global_variables as gv

class AutoPilot:
    def __init__(self, pin):
        self.pin = pin
        # self.run = False
        factory = PiGPIOFactory()
        self.servo = Servo(self.pin, pin_factory=factory)
        self.servo.value = 0
        
    def operate(self):
        def process():
            direction = 1
            self.servo.value = 0
            while gv.run:
                # print(f'gv.autopilot: {gv.autopilot}')
                if gv.autopilot:
                    if self.servo.value > .8 or self.servo.value < -.8:
                        direction = direction * -1
                    self.servo.value = self.servo.value + .015 * direction
                    sleep(.005)
                else:
                    sleep(.01)
        Process(target=process).start()
           
if __name__ == "__main__":
    gv.run = True
    gv.autopilot = True
    autopilot = AutoPilot(27)
    print('Starting...')
    autopilot.operate()
    sleep(5)
    print('Pausing autopilot...')
    gv.autopilot = False
    sleep(3)
    print('Resuming autopilot...')
    gv.autopilot = True
    sleep(5)
    gv.autopilot = False
    gv.run = False
    print('Stopping.')






# import RPi.GPIO as GPIO
# import time
# import random
# from threading import Thread
# 
# def handle_servo():
#     def thread():
#         GPIO.setmode(GPIO.BOARD)
#         GPIO.setup(11, GPIO.OUT)
#         servo1 = GPIO.PWM(11,50)
#         servo1.start(0)
#         print('waiting for 2 seconds')
#         time.sleep(2)
# 
#         while True:
#             servo1.ChangeDutyCycle(7)
#             time.sleep(1)
#             servo1.ChangeDutyCycle(10)
#             time.sleep(1)
#             servo1.ChangeDutyCycle(7)
#             time.sleep(1)
#             servo1.ChangeDutyCycle(4)
#             time.sleep(1)
# 
#         servo1.ChangeDutyCycle(7)
#         time.sleep(1)
#         servo1.stop()
#         GPIO.cleanup()
#         print("All Done!")
#     Thread(target=thread).start()
#     
# if __name__ == "__main__":
#     handle_servo()

# direction = 1
# duty = 7
# direction_changes = 0
# while direction_changes < 40:
#     if direction_changes % 10 == 0:
#         increment = random.uniform(.2, .5)
#     
#     time.sleep(.03)
#     duty = duty + increment * direction
#     servo1.ChangeDutyCycle(duty)
#     
#     if duty < 5 or duty > 9:
#         direction = direction * -1
#         direction_changes += 1
#         
# servo1.ChangeDutyCycle(7)
# time.sleep(1)
# servo1.stop()
# GPIO.cleanup()
# print("All Done!")
    