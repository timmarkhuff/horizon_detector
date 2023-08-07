import time

from utils.messages import ParsedPacket
from .read_sbus_from_GPIO import SbusReader

class ReceiverError(Exception):
    pass

class Receiver:
    def __init__(self, config: ParsedPacket):
        self.config = config

        # Capture the channels as object attributes. This should make accessing the values more performant.
        # Subtracting 1 from each channel because the channels are 1-indexed in the config file, but 0-indexed in the packet.
        # Sticks
        self.ail_ch = config.channels.sticks.ail - 1
        self.ele_ch = config.channels.sticks.ele - 1
        self.thr_ch = config.channels.sticks.thr - 1
        self.rud_ch = config.channels.sticks.rud - 1

        # Trim
        self.ail_trim_ch = config.channels.trim.ail - 1
        self.ele_trim_ch = config.channels.trim.ele - 1
        self.rud_trim_ch = config.channels.trim.rud - 1

        # Switches
        self.recording_switch_ch = config.channels.switches.rec - 1
        self.autopilot_switch_ch = config.channels.switches.auto - 1

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
            
    def _pwm_to_continuous(self, pwm: float, reversed: bool = False) -> float:
        """Takes a PWM value and converts it into a continuous value between -1 and 1
        """
        if pwm < self.config.pwm.min:
            ret_val =  -1
        elif pwm > self.config.pwm.max:
            ret_val = 1
        else:
            ret_val = (pwm - self.config.pwm.min) / self.PWM_RANGE * 2 - 1

        # Reverse the value if necessary
        if reversed:
            return -ret_val
        else:
            return ret_val
        
    def get_parsed_packet(self) -> ParsedPacket:
        # Get raw packet
        packet = self.reader.translate_latest_packet()

        # Parse the packet
        # Sticks 
        self.parsed_packet.sticks.ail = self._pwm_to_continuous(packet[self.ail_ch])
        self.parsed_packet.sticks.ele = self._pwm_to_continuous(packet[self.ele_ch])
        self.parsed_packet.sticks.thr = self._pwm_to_continuous(packet[self.thr_ch])
        self.parsed_packet.sticks.rud = self._pwm_to_continuous(packet[self.rud_ch])

        # Trim
        self.parsed_packet.trim.ail = self._pwm_to_continuous(packet[self.ail_trim_ch])
        self.parsed_packet.trim.ele = self._pwm_to_continuous(packet[self.ele_trim_ch])
        self.parsed_packet.trim.rud = self._pwm_to_continuous(packet[self.rud_trim_ch])

        # Switches
        self.parsed_packet.switches.rec = self._pwm_to_continuous(packet[self.recording_switch_ch])
        self.parsed_packet.switches.auto = self._pwm_to_continuous(packet[self.autopilot_switch_ch])
        
        return self.parsed_packet



