import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
from time import sleep

class TransmitterSwitch:
    def __init__(self, pi, gpio, positions: int, weighting=0.0):
        """
        Instantiate with the Pi and gpio of the PWM signal
        to monitor.

        Optionally a weighting may be specified.  This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading.  It defaults to 0 which means
        the old reading has no effect.  This may be used to
        smooth the data.
        """
        self.pi = pi
        self.gpio = gpio
        self.positions = positions
        
        # determine the thresholds for the button positions
        pwm_min = 988
        pwm_max = 2010
        increment = (pwm_max - pwm_min) / self.positions
        thresh = pwm_min
        self.position_thresholds = []
        for n in range(self.positions - 1):
            thresh += increment
            self.position_thresholds.append(thresh)
            
        # apply weighting
        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99

        self._new = 1.0 - weighting # Weighting for new reading.
        self._old = weighting       # Weighting for old reading.

        self._high_tick = None
        self._period = None
        self._high = None

        pi.set_mode(gpio, pigpio.INPUT)
        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)
        
        # initialize the previous position
        sleep(.1) # some extra time to allow things to initialize
        self.previous_position = self.get_current_position()
        
    def _cbf(self, gpio, level, tick):
        if level == 1:
            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)
                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t

            self._high_tick = tick

        elif level == 0:
            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)

                if self._high is not None:
                   self._high = (self._old * self._high) + (self._new * t)
                else:
                   self._high = t

    def get_pulse_width(self):
        """
        Returns the PWM pulse width in microseconds.
        """
        if self._high is not None:
            return self._high
        else:
            return 0.0
        
    def get_current_position(self) -> int:
        """
        Returns the current position of the switch
        """
        # get the pulse width
        pw = self.get_pulse_width()
        
        # correlate the pulse width to a button position
        for n in range(self.positions - 1):
            if pw < self.position_thresholds[n]:
                current_position = n
                break
        else:
            current_position = self.positions - 1
            
        return current_position
    
    def detect_position_change(self) -> int:
        """
        Checks if the button position has changed from the previous call.
        If so, the new position is returned.
        If not, None is returned.
        """
        current_position = self.get_current_position()
        
        # check if the position has changed
        if current_position == self.previous_position:
            new_position = None
        else:
            new_position = current_position
        
        # update self.previous_position for next call of this function
        self.previous_position = current_position
        
        # return the result
        return new_position
                    
    def release(self):
        """
        Releases resources.
        """
        self._cb.cancel()

# Demo
if __name__ == '__main__':
    from time import sleep
    
    # define the transmitter switch
    pi = pigpio.pi()
    gpio = 22
    switch = TransmitterSwitch(pi, gpio, 2)
    
    # initialize some values for diagnostics
    max_pwm = 0
    min_pwm = 1000000
    
    # start demo
    print('Demo starting...')
    for n in range(100):
        sleep(.1)
        pw = switch.get_pulse_width()
        current_position = switch.get_current_position()
        new_position = switch.detect_position_change()
        
        print(f'pulse width: {pw} | current_position: {current_position} | new_position: {new_position}')
        print('-----------------------------')
        
        # update max and min PWM values
        if pw > max_pwm:
            max_pwm = pw
        if pw < min_pwm:
            min_pwm = pw
    
    print('Demo finished.')
    print(f'min_pwm: {min_pwm}')
    print(f'max_pwm: {max_pwm}')


        
        
        
        
        
        