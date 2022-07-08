# read_PWM.py
# 2015-12-08
# Public Domain
# source: https://abyz.me.uk/rpi/pigpio/examples.html

import time
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html

class reader:
   """
   A class to read PWM pulses and calculate their frequency
   and duty cycle.  The frequency is how often the pulse
   happens per second.  The duty cycle is the percentage of
   pulse high time per cycle.
   """
   def __init__(self, pi, gpio, weighting=0.0):
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

   def frequency(self):
      """
      Returns the PWM frequency.
      """
      if self._period is not None:
         return 1000000.0 / self._period
      else:
         return 0.0

   def pulse_width(self):
      """
      Returns the PWM pulse width in microseconds.
      """
      if self._high is not None:
         return self._high
      else:
         return 0.0

   def duty_cycle(self):
      """
      Returns the PWM duty cycle percentage.
      """
      if self._high is not None:
         return 100.0 * self._high / self._period
      else:
         return 0.0

   def cancel(self):
      """
      Cancels the reader and releases resources.
      """
      self._cb.cancel()

if __name__ == "__main__":
    import time
    import pigpio
    import read_PWM

    PWM_GPIO = 4
    RUN_TIME = 10
    SLEEP_TIME = .1

    pi = pigpio.pi()

    p = read_PWM.reader(pi, PWM_GPIO)

    start = time.time()

    max_pw = 0
    min_pw = 1000000
    max_duty = 0
    min_duty = 1000000
    while (time.time() - start) < RUN_TIME:
        time.sleep(SLEEP_TIME)

        f = p.frequency()
        pw = p.pulse_width()
        dc = p.duty_cycle()
    
        if pw > max_pw:
            max_pw = pw
        elif pw < min_pw:
            min_pw = pw
            
        if dc > max_duty:
            max_duty = dc
        elif dc < min_duty:
            min_duty = dc
            
        average_pw = (max_pw - min_pw) / 2 + min_pw
        average_duty = (max_duty - min_duty) / 2 + min_duty
          
        
        print("f={:.1f} pw={} dc={:.2f}".format(f, int(pw+0.5), dc))

    p.cancel()
    pi.stop()
    print('Finished demo')
    print(f'max_pw: {max_pw}')
    print(f'min_pw: {min_pw}')
    print(f'average_pw: {average_pw}')
    print(f'max_duty: {max_duty}')
    print(f'min_duty: {min_duty}')
    print(f'average_duty: {average_duty}')


