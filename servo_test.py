from gpiozero import Servo
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory
from threading import Thread


sleep(1)

def handle_servo():
    def thread():
        factory = PiGPIOFactory()
        servo = Servo(17, pin_factory=factory)
        servo.value = 0
        sleep(2)

        while True:
            servo.value = .5
            sleep(1)
            servo.value = 0
            sleep(1)
            servo.value = -.5
            sleep(1)
            servo.value = 0
            sleep(1)

        servo.value = 0
        time.sleep(1)
        print("All Done!")
    Thread(target=thread).start()
    
if __name__ == "__main__":
    handle_servo()






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
    