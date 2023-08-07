from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory

from time import time
import numpy as np

from utils.messages import Message

class FlightController:
    def __init__(self, config: dict):
        self.config = config

        # Set up the servos
        factory = PiGPIOFactory()
        self.ail_servo = Servo(config['rpi/output_pins/ail'], pin_factory=factory)
        self.ele_servo = Servo(config['rpi/output_pins/ele'], pin_factory=factory)
        self.rud_servo = Servo(config['rpi/output_pins/rud'], pin_factory=factory)
        self.msg = Message()

    def run(self, packet: Message, sensor_msg: Message):
        pass

    def select_program(self, program_id: int) -> None:
        pass

    def release(self) -> None:
        # release the servos?
        pass
