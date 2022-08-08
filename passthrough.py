from time import sleep
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import pigpio
from switches_and_servos import TransmitterSwitch
import read_PWM

# global constants
MIN_DUTY = 3.84
MAX_DUTY = 9.76
DUTY_RANGE = MAX_DUTY - MIN_DUTY

def duty_to_value(duty) -> float:
    if duty < MIN_DUTY:
        servo_value = -1
    elif duty > MAX_DUTY:
        servo_value = 1
    else:
        servo_value = (duty - MIN_DUTY) / DUTY_RANGE
        servo_value = (servo_value - .5) * 2
    return servo_value   
    
# create TransmitterSwitch object
pi = pigpio.pi()
gpio = 22
autopilot_switch = TransmitterSwitch(pi, gpio, 2)

# define servos
factory = PiGPIOFactory()
servo = Servo(18, pin_factory=factory)
sleep(1)
servo.value = 0

# PWM reader
gpio = 4
reader = read_PWM.reader(pi, gpio)
sleep(1)

current_servo_value = duty_to_value(reader.duty_cycle())
previous_servo_value = current_servo_value

autopilot = False
direction = 1
increment = .1
wait_time = 1/30
while True:
    sleep(wait_time)
    
    # read controls
    current_duty = reader.duty_cycle()   
    current_servo_value = duty_to_value(current_duty)
    # filter out small movements to avoid jitter
    if abs(current_servo_value - previous_servo_value) / 2 < .05:
        current_servo_value = previous_servo_value        
      
    # process switch input
    new_switch_position = autopilot_switch.detect_position_change()
    if new_switch_position == 1:
        autopilot = True
    elif new_switch_position == 0:
        autopilot = False
    
    # run autopilot
    if autopilot:
        # determine the next value
        next_value = servo.value + increment * direction
        if next_value >= 1 or next_value <= -1:
            direction = direction * -1
        # actuate the servo
        servo.value = servo.value + increment * direction
    
    # actuate servos
    if not autopilot:
        servo.value = current_servo_value
        
    # update values for next function call
    previous_servo_value = current_servo_value
    
    
    
    
    
