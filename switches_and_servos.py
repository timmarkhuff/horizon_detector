import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import numpy as np

# global pi object for all TransmitterControl objects to use
PI = pigpio.pi()

class TransmitterControl:
    def __init__(self, input_pin, weighting):
        """
        Instantiate with input_pin of the PWM signal
        to monitor.
        Optionally a weighting may be specified.  This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading.  It defaults to 0 which means
        the old reading has no effect.  This may be used to
        smooth the data.
        """
        self.input_pin = input_pin
        
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

        PI.set_mode(input_pin, pigpio.INPUT)
        self._cb = PI.callback(input_pin, pigpio.EITHER_EDGE, self._cbf)
        
        # initialize the previous position
        sleep(.1) # some extra time to allow things to initialize
        
    def _cbf(self, input_pin, level, tick):
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
        
    def get_duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        if self._high is not None:
            return 100.0 * self._high / self._period
        else:
            return 0.0
        
    def release(self):
        """
        Releases resources.
        """
        self._cb.cancel()

class TransmitterSwitch(TransmitterControl):
    def __init__(self, input_pin, positions: int, weighting=0.0):
        """        
        positions: the number of positions that the switch has (usually 2 or 3)
        """
        super().__init__(input_pin, weighting)
        self.positions = positions
        
        # determine the thresholds for the button positions
        pwm_min = 860 # originally 988 for 2 positions switches
        pwm_max = 2140 # originally 2010 for 2 positions switches
        increment = (pwm_max - pwm_min) / self.positions
        thresh = pwm_min
        self.position_thresholds = []
        for n in range(self.positions - 1):
            thresh += increment
            self.position_thresholds.append(thresh)
                    
        # initialize the previous position
        self.previous_position = self.get_current_position()
        
        
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
    
class ServoHandler(TransmitterControl):
    def __init__(self, input_pin, output_pin, fps, smoothing_dur=0, increments=None, weighting=0.0):
        """
        smoothing_dur: the duration (in seconds) of servo reading smoothing.
        increments: the number of discrete increments to which the servo can be moved.
        """
        super().__init__(input_pin, weighting=0.0)
        
        self.min_duty = 7.3 # 3.84
        self.max_duty = 12.9 # 9.76
        self.duty_range = self.max_duty - self.min_duty
        
        # define servo
        factory = PiGPIOFactory()
        self.servo = Servo(output_pin, pin_factory=factory)
        
        # anti-jitter smoothing settings
        recent_servo_readings_list_len = int(np.round(fps * smoothing_dur))
        if recent_servo_readings_list_len > 1:
            self.smoothing = True            
            self.recent_servo_readings = [0 for n in range(recent_servo_readings_list_len)]
        else:
            self.smoothing = False
            
        # anti-jitter increments
        self.previous_actuated_value = 0 # initialize at center
        if increments:
            self.incremental_movement = True
            # 2 is the full range of servo movement (-1 to 1)
            full_range = 2
            self.increment_length = full_range / increments
        else:
            self.incremental_movement = False

                
    def duty_to_servo_value(self, duty) -> float:
        if duty < self.min_duty:
            servo_value = -1
        elif duty > self.max_duty:
            servo_value = 1
        else:
            servo_value = (duty - self.min_duty) / self.duty_range
            servo_value = (servo_value - .5) * 2
        
        return servo_value
    
    def actuate(self, servo_value):
        # optional anti-jitter filter
        if self.incremental_movement:
            if abs(servo_value - self.previous_actuated_value) < self.increment_length:
                return self.previous_actuated_value
            else:
                self.previous_actuated_value = servo_value
                
        # actuate servo
        self.servo.value = servo_value
        
        # return the value that was actually actuated
        return servo_value
        
    def read(self):       
        servo_duty = self.get_duty_cycle()
        servo_value = self.duty_to_servo_value(servo_duty)
        # print(f'{servo_duty} | {servo_value}')
        
        # optional smoothing
        if self.smoothing:
            self.recent_servo_readings.append(servo_value)
            del self.recent_servo_readings[0]
            servo_value = np.average(self.recent_servo_readings)
        
        return servo_value                 
                              
# Demo
if __name__ == '__main__':
    from time import sleep
    from timeit import default_timer as timer
    
    # globals
    FPS = 30
    WAIT_TIME = 1 / FPS
    autopilot = False
    
    # define the transmitter switch
    input_pin = 26
    switch = TransmitterSwitch(input_pin, 2)
    
    # define servo handler
    input_pin = 4
    output_pin = 18
    servo_handler = ServoHandler(input_pin, output_pin)
    
    # initialize some values for diagnostics
    max_pwm = 0
    min_pwm = 1000000
    
    # start demo
    t1 = timer()
    print('Demo starting...')
    n = 0
    while True:
        # assess the timer
        t2 = timer()
        if t2 - t1 > 60:
            break
        # wait
        sleep(WAIT_TIME)
        
        # read the switch
        pw = switch.get_pulse_width()
        current_position = switch.get_current_position()
        new_position = switch.detect_position_change()
        
        # print out the switch reading every second
        if n % FPS == 0:
            print(f'pulse width: {pw} | current_position: {current_position} | new_position: {new_position}')
            print('-----------------------------')
        
            # update max and min PWM values
            if pw > max_pwm:
                max_pwm = pw
            if pw < min_pwm:
                min_pwm = pw
        
        # toggle autopilot
        if new_position == 1:
            autopilot = True
        elif new_position == 0:
            autopilot = False
        
        if autopilot:
            pass
        else:
            servo_handler.passthrough()     

        # increment iteration number
        n += 1
    
    print('Demo finished.')
    print(f'min_pwm: {min_pwm}')
    print(f'max_pwm: {max_pwm}')