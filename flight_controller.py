# libraries
import numpy as np
from simple_pid import PID
import random
from timeit import default_timer as timer

FULL_ROTATION = 360

# dummy functions
def actuate_servo(pin, value):
    return f'Actuating servo {pin} to {value}'

# classes
class GPIOSimulator:
    def __init__(self):
        self.pins = {}
    def add_pin(self, pin):
        self.pins[pin] = 0 # inialize with value of zero
    def update_pin_value(self, pin, value):
        self.pins[pin] = value
    def read_gpio(self, pin):
        return self.pins[pin]

class Wind:
    def __init__(self, speed_range):
        self.speed_range = speed_range
        self.t1 = timer()
        self.t2 = self.t1
        self.randomize()
        
    def randomize(self):
        self.seconds_until_next_change = random.randint(1,25)
        self.speed = random.uniform(-1 * self.speed_range, self.speed_range)
        print('-----------------')
        print(f'Wind speed changing to {self.speed}.')

    def run(self):
        self.t2 = timer()
        if self.t2 - self.t1 > self.seconds_until_next_change:
            self.randomize()
            self.t1 = timer()

class FlightController:
    def __init__(self, ail_pin_in, ail_pin_out, elev_pin_in, elev_pin_out, fps, gpio_simulator=None):
        self.ail_pin_in = ail_pin_in
        self.ail_pin_out = ail_pin_out
        self.elev_pin_in = elev_pin_in
        self.elev_pin_out = elev_pin_out
        self.gpio_simulator = gpio_simulator
        self.fps = fps

        # constants
        self.INTERRUPTABLE_PROGRAMS = [1, 2]
        self.INTERRUPT_THRESH = .1

        # set the default flight program
        self.select_program(1)

        # keep track of recent detection scores for n second(s)
        n = 1 # seconds
        self.horizon_detection_arr = [0 for n in range(n * fps)]

    def run(self, roll, pitch, is_good_horizon):
        """
        Run this for each iteration of main loop.
        Takes roll, pitch and is_good_horizon, and runs the FlightProgram
        accordingly.
        """

        # store some values
        self.convert_roll(roll)
        self.pitch = pitch
        self.is_good_horizon = is_good_horizon

        # update the array of horizon detection results
        self.horizon_detection_arr.append(is_good_horizon)
        del self.horizon_detection_arr[0]

        # read stick values
        self.ail_stick_value = self.read_gpio(self.ail_pin_in)
        self.elev_stick_value = self.read_gpio(self.elev_pin_in)

        # run the flight program
        stop = self.program.run()

        # switch back to manual flight if the current program has ended
        if stop:
            self.select_program(0)
        
        # check for user interruption
        if self.program_id in self.INTERRUPTABLE_PROGRAMS:
            if abs(self.ail_stick_value) > self.INTERRUPT_THRESH or \
               abs(self.elev_stick_value) > self.INTERRUPT_THRESH:
                # return to manual control
                self.select_program(0)

        # actuate the servos
        actuate_servo(self.ail_pin_out, self.ail_val)
        actuate_servo(self.elev_pin_out, self.elev_val)

        return self.ail_val, self.elev_val

    def select_program(self, program_id):
        self.program = FlightProgram.__subclasses__()[program_id](self)
        self.program_id = program_id
        print('-----------------')
        print(f'Starting program: {self.program.__class__.__name__}')

    def read_gpio(self, pin):
        return self.gpio_simulator.read_gpio(pin)

    def convert_roll(self, roll):
        if roll > FULL_ROTATION / 2:
            roll -= FULL_ROTATION
        self.roll = roll

class FlightProgram:
    def __init__(self, flt_ctrl):
        """
        Metaclass for flight programs.
        """
        self.flt_ctrl = flt_ctrl
        self.flt_ctrl.program = self
        self.stop = False

class ManualFlight(FlightProgram):
    def __init__(self, flt_ctrl):
        """
        User controls the aircraft.
        """
        super().__init__(flt_ctrl)
    
    def run(self):
        # aileron 
        self.flt_ctrl.ail_val = self.flt_ctrl.ail_stick_value

        # aileron 
        self.flt_ctrl.elev_val = self.flt_ctrl.elev_stick_value

        return False

class SurfaceCheck(FlightProgram):
    def __init__(self, flt_ctrl):
        """
        Automatic surface check for preflight check.
        """
        super().__init__(flt_ctrl)

        # initialize the control surfaces in netural positions
        self.flt_ctrl.ail_val = .01
        self.flt_ctrl.elev_val = .01
        self.ail_val_prev = self.flt_ctrl.ail_val
        self.elev_val_prev = self.flt_ctrl.elev_val

        # some values for moving the servos
        self.direction = 1
        self.increment = 1 / self.flt_ctrl.fps * 3
        self.ail_iterations = 0
        self.elev_iterations = 0

        # constants
        self.ITERATIONS = 7
    
    def run(self):
        if self.ail_iterations < self.ITERATIONS:
            self.flt_ctrl.elev_val = 0
            if abs(self.flt_ctrl.ail_val + self.increment * self.direction) > 1:
                self.direction *= -1
            self.flt_ctrl.ail_val += (self.increment * self.direction)
            if np.sign(self.flt_ctrl.ail_val) != np.sign(self.ail_val_prev):
                self.ail_iterations += 1
        elif self.elev_iterations < self.ITERATIONS:
            self.flt_ctrl.ail_val = 0
            if abs(self.flt_ctrl.elev_val + self.increment * self.direction) > 1:
                self.direction *= -1
            self.flt_ctrl.elev_val += (self.increment * self.direction)
            if np.sign(self.flt_ctrl.elev_val) != np.sign(self.elev_val_prev):
                self.elev_iterations += 1 
        else:
            self.flt_ctrl.ail_val
            self.flt_ctrl.elev_val = 0
            self.stop = True

        # remember previous values for next iteration
        self.ail_val_prev = self.flt_ctrl.ail_val
        self.elev_val_prev = self.flt_ctrl.elev_val

        return self.stop

class LevelFlight(FlightProgram):
    def __init__(self, flt_ctrl):
        """
        Keeps the plane level.
        """
        super().__init__(flt_ctrl)

        # PID controllers
        # default: 1, .1, .05
        # works well: .8, .1, .02
        # aileron
        self.ail_pid = PID(1, .1, .02, setpoint=0) 
        self.ail_pid.output_limits = (-1, 1)
        self.ail_pid.sample_time = 1 / self.flt_ctrl.fps
        # elevator
        self.elev_pid = PID(.6, .2, .02, setpoint=0) 
        self.elev_pid.sample_time = 1 / self.flt_ctrl.fps 
        self.elev_pid.output_limits = (-1, 1)
    
    def run(self):
        if self.flt_ctrl.is_good_horizon:
            # update some values
            self.flt_ctrl.ail_val = self.ail_pid(self.flt_ctrl.roll)
            self.flt_ctrl.elev_val = self.elev_pid(-1 * self.flt_ctrl.pitch)
        elif not any(self.flt_ctrl.horizon_detection_arr):
            # return to neutral position after a period of time
            self.flt_ctrl.ail_val = 0 
            self.flt_ctrl.elev_val = 0
        return False

def main():
    import cv2
    from draw_display import draw_horizon, draw_surfaces

    FPS = 30
    WAIT_TIME = int(np.round(1 / FPS * 1000))
    FOV = 48.8

    wind = Wind(.2)
    gpio_simulator = GPIOSimulator()
    flt_ctrl = FlightController(1, 11, 2, 13, FPS, gpio_simulator)
    gpio_simulator.add_pin(flt_ctrl.ail_pin_in)
    gpio_simulator.add_pin(flt_ctrl.elev_pin_in)

    canvas = np.zeros((480, 640, 3), dtype = "uint8")

    ail_val = 0
    elev_val = 0
    roll = .0001
    pitch = 0

    is_good_horizon = True
    draw_ground_line = True

    n = 0
    while True:     
        # copy the canvas to draw on it
        canvas_copy = canvas.copy()

        # Simulation: get fake roll and pitch numbers, for displaying
        # when no horizon is detected.
        if n % (FPS//4) == 0:
            fake_roll = random.uniform(0,1)
            fake_pitch= random.uniform(0,1)

        # initialize some values
        ail_stick_value = 0
        elev_stick_value = 0

        # Simulation: update roll and pitch
        wind.run()
        roll += ail_val
        roll = roll % FULL_ROTATION
        pitch -= elev_val + wind.speed

        # run flight controller
        ail_val, elev_val = flt_ctrl.run(roll, pitch, is_good_horizon)

        # draw
        if is_good_horizon:
            color = (255,0,0)
            draw_ground_line = True
            draw_horizon(canvas_copy, roll, pitch, FOV, color, draw_ground_line)
        else:
            color = (0,0,255)
            draw_ground_line = False
            draw_horizon(canvas_copy, fake_roll, fake_pitch, FOV, color, draw_ground_line)

        # draw surfaces
        if flt_ctrl.program_id in [1,2]:
            color = (0,255,0)
        else:
            color = (0,0,255)
        draw_surfaces(canvas_copy, .7, .95, .83, .9, ail_val, elev_val, color)

        # center circle
        center = (canvas_copy.shape[1]//2, canvas_copy.shape[0]//2)
        radius = canvas_copy.shape[0]//100
        cv2.circle(canvas_copy, center, radius, (255,0,0), 2)

        # FlightProgram type
        program_name = flt_ctrl.program.__class__.__name__
        cv2.putText(canvas_copy, program_name, (20,40),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,200,200),1,cv2.LINE_AA)

        # show some results
        cv2.imshow("Flight Controller", canvas_copy)

        # wait
        key = cv2.waitKey(WAIT_TIME)
        
        if key == ord('q'):
            break
        elif key == ord('a'):
            ail_stick_value = -.5
        elif key == ord('d'):
            ail_stick_value = .5
        elif key == ord('w'):
            elev_stick_value = .5
        elif key == ord('s'):
            elev_stick_value = -.5
        elif key == ord('r'):
            pitch = 0
        elif key == ord('1'):
            flt_ctrl.select_program(1)
        elif key == ord('2'):
            flt_ctrl.select_program(2)
        elif key == ord('h'):
            is_good_horizon = not is_good_horizon
            if not is_good_horizon:
                print('Horizon signal lost.')
            else:
                print('Horizon signal restored.')
        
        # Simulation: get some gpio values in response to the buttons that were pressed
        gpio_simulator.update_pin_value(flt_ctrl.ail_pin_in, ail_stick_value)
        gpio_simulator.update_pin_value(flt_ctrl.elev_pin_in, elev_stick_value)
        
        # increment the frame count
        n += 1

    print('-----------------')
    print('Finished')
    print('-----------------')

# run the demo
if __name__ == "__main__":
    main()