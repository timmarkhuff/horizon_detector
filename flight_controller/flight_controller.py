from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory

from utils.messages import Message

from .flight_program import ManualFlightProgram, SurfaceCheckProgram

INTERRUPT_THRESHOLD = .07

class FlightController:
    def __init__(self, config: dict):

        # Set up the servos
        factory = PiGPIOFactory()
        self.ail_servo = Servo(config.output_pins.ail, pin_factory=factory)
        self.ele_servo = Servo(config.output_pins.ele, pin_factory=factory)
        self.rud_servo = Servo(config.output_pins.rud, pin_factory=factory)

        self.flight_program = SurfaceCheckProgram()

    def run(self, packet: Message, sensor_msg: Message) -> Message:
        # Check  if the user is trying to interrupt the program. If so, return
        # to manual flight mode
        if self.flight_program.is_interruptable():
            if abs(packet.sticks.ail) > INTERRUPT_THRESHOLD or \
                abs(packet.sticks.ele) > INTERRUPT_THRESHOLD or \
                abs(packet.sticks.rud) > INTERRUPT_THRESHOLD:
                self.flight_program = ManualFlightProgram()

        # Run the flight program
        is_finished, output_msg = self.flight_program.run(packet, sensor_msg)

        # Actuate the servos
        self.ail_servo.value = output_msg.ail
        self.ele_servo.value = output_msg.ele
        self.rud_servo.value = output_msg.rud

        # Check if the program has finished, revert back to manual flight if it has
        if is_finished:
            self.flight_program = ManualFlightProgram()

        return output_msg

    def release(self) -> None:
        # release the servos?
        pass
