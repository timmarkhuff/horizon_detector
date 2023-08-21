from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from utils.messages import Message

flight_program_output = Message()

class FlightProgram(ABC):
    """Base class for flight programs
    """
    id_counter = 0

    @abstractmethod
    def is_interruptable(self) -> bool:
        pass

    @abstractmethod
    def run(self, packet: Message, sensor_msg: Message) -> Tuple[bool, Message]:
        pass

    def _restrict(self, value: float) -> float:
        if value < -1:
            return -1
        elif value > 1:
            return 1
        else:
            return value


class ManualFlightProgram(FlightProgram):
    """User controls the aircraft
    """
    program_id = FlightProgram.id_counter
    FlightProgram.id_counter += 1

    def is_interruptable(self) -> bool:
        return False
    
    def run(self, packet: Message, sensor_msg: Message) -> Tuple[bool, Message]:
        flight_program_output.ail = self._restrict(packet.sticks.ail + packet.trim.ail)
        flight_program_output.ele = self._restrict(packet.sticks.ele + packet.trim.ele)
        flight_program_output.rud = self._restrict(packet.sticks.rud + packet.trim.rud)
        flight_program_output.program_id = self.program_id

        return False, flight_program_output
    
class SurfaceCheckProgram(FlightProgram):
    """Performs a quick surface check
    """
    program_id = FlightProgram.id_counter
    FlightProgram.id_counter += 1

    # Create arrays that represent the surface check pattern
    amplitude = .6 # max servo deflection
    sampling_frequency = 30 # should equal FPS of main loop
    wave_length = .7 # time in seconds of each movement
    duration = wave_length * 2 # duration of each segment
    num_samples = int(duration * sampling_frequency)
    time = np.linspace(0, duration, num_samples)
    sine_wave = amplitude * np.sin(2 * np.pi * (1/wave_length) * time)
    zeros = np.zeros(len(sine_wave))
    
    AIL_PATTERN = np.concatenate((sine_wave, sine_wave, zeros, zeros, sine_wave)).tolist()
    ELE_PATTERN = np.concatenate((sine_wave, zeros, sine_wave, zeros, sine_wave)).tolist()
    RUD_PATTERN = np.concatenate((sine_wave, zeros, zeros, sine_wave, sine_wave)).tolist()

    TOTAL_ITERATIONS = len(AIL_PATTERN)

    def __init__(self) -> None:
        self.current_iteration = 0

    def is_interruptable(self) -> bool:
        return True
    
    def run(self, packet: Message, sensor_msg: Message) -> Tuple[bool, Message]:
        flight_program_output.ail = self.AIL_PATTERN[self.current_iteration]
        flight_program_output.ele = self.ELE_PATTERN[self.current_iteration]
        flight_program_output.rud = self.RUD_PATTERN[self.current_iteration]
        flight_program_output.program_id = self.program_id

        self.current_iteration += 1

        if self.current_iteration == self.TOTAL_ITERATIONS:
            return True, flight_program_output
        else:
            return False, flight_program_output

class QuickWiggleProgram(FlightProgram):
    """Performs a quick confirmation wiggle of the servos
    """
    program_id = FlightProgram.id_counter
    FlightProgram.id_counter += 1

    def is_interruptable(self) -> bool:
        return True
    
    def run(self, packet: Message, sensor_msg: Message) -> Tuple[bool, Message]:
        flight_program_output.ail = .1
        flight_program_output.ele = .1
        flight_program_output.rud = .1
        flight_program_output.program_id = self.program_id

        return False, flight_program_output
    
