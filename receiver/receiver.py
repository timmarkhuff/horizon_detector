import time

from utils.messages import ParsedPacket
from .read_sbus_from_GPIO import SbusReader

class ReceiverError(Exception):
    pass

class Receiver:
    def __init__(self, config: ParsedPacket):

        # Capture the configurations as object attributes. This should make accessing the values more performant.
        # Subtracting 1 from each channel because the channels are 1-indexed in the config file, but 0-indexed in the packet.

        self.PWM_MIN = config.pwm.min
        self.PWM_MAX = config.pwm.max

        # Sticks channels
        self.ail_ch = config.controls.sticks.ail.channel - 1
        self.ele_ch = config.controls.sticks.ele.channel - 1
        self.thr_ch = config.controls.sticks.thr.channel - 1
        self.rud_ch = config.controls.sticks.rud.channel - 1

        # Stick direction
        self.ail_dir = 1 if not config.controls.sticks.ail.reversed else -1
        self.ele_dir = 1 if not config.controls.sticks.ele.reversed else -1
        self.thr_dir = 1 if not config.controls.sticks.thr.reversed else -1
        self.rud_dir = 1 if not config.controls.sticks.rud.reversed else -1

        # Trim channels
        self.ail_trim_ch = config.controls.sticks.ail.trim_channel - 1
        self.ele_trim_ch = config.controls.sticks.ele.trim_channel - 1
        self.rud_trim_ch = config.controls.sticks.rud.trim_channel - 1
        self.trim_scaling = config.controls.trim_scaling

        # Switches channels
        self.recording_switch_ch = config.controls.switches.rec.channel - 1
        self.autopilot_switch_ch = config.controls.switches.auto.channel  - 1

        self.PWM_RANGE = config.pwm.max - config.pwm.min

        self.reader = SbusReader(config.rpi.input_pins.sbus)

        self.parsed_packet = ParsedPacket()

    def connect(self, timeout: float = 10.0) -> None:
        """Attempts to connect to the receiver. If a connection is not made within
        timeout seconds, a ReceiverError is raised.
        """
        self.reader.begin_listen()
        start_time = time.time()
        while not self.reader.is_connected():
            if time.time() - start_time > timeout:
                raise ReceiverError(
                    f'Timeout while waiting for receiver to connect after {timeout} seconds.'
                    )
            
    def _pwm_to_continuous(self, pwm: float) -> float:
        """Takes a PWM value and converts it into a continuous value between -1 and 1
        """
        if pwm < self.PWM_MIN:
            return -1
        elif pwm > self.PWM_MAX:
            return 1
        else:
            return (pwm - self.PWM_MIN) / self.PWM_RANGE * 2 - 1

    def _pwm_to_position(self, pwm: int, num_positions: int = 2) -> int:
        """Converts a PWM value to a switch position.

        num_postions: the total number of positions of the switch
        """
        if pwm <= self.PWM_MIN:
            return  0
        elif pwm >= self.PWM_MAX:
            return num_positions - 1
        else:
            return int(round((pwm - self.PWM_MIN) / (self.PWM_RANGE) * (num_positions - 1)))
        
    def get_parsed_packet(self) -> ParsedPacket:
        # Get raw packet
        packet = self.reader.translate_latest_packet()

        # Parse the packet
        # Sticks 
        self.parsed_packet.sticks.ail = self._pwm_to_continuous(packet[self.ail_ch]) * self.ail_dir
        self.parsed_packet.sticks.ele = self._pwm_to_continuous(packet[self.ele_ch]) * self.ele_dir
        self.parsed_packet.sticks.thr = self._pwm_to_continuous(packet[self.thr_ch]) * self.thr_dir
        self.parsed_packet.sticks.rud = self._pwm_to_continuous(packet[self.rud_ch]) * self.rud_dir

        # Trim
        self.parsed_packet.trim.ail = self._pwm_to_continuous(packet[self.ail_trim_ch]) * self.ail_dir * self.trim_scaling
        self.parsed_packet.trim.ele = self._pwm_to_continuous(packet[self.ele_trim_ch]) * self.ele_dir * self.trim_scaling
        self.parsed_packet.trim.rud = self._pwm_to_continuous(packet[self.rud_trim_ch]) * self.rud_dir * self.trim_scaling

        # Switches
        self.parsed_packet.switches.rec = self._pwm_to_position(packet[self.recording_switch_ch], 2)
        self.parsed_packet.switches.auto = self._pwm_to_position(packet[self.autopilot_switch_ch], 2)
        
        return self.parsed_packet



