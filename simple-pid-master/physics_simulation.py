import cv2
import numpy as np
import random
from simple_pid import PID
from timeit import default_timer as timer

class Rectangle:
    def __init__(self, mass):
        self.mass = mass
        self.pos_x = 100
        self.pos_y = 250
        self.width = 75
        self.height = 50
        self.velocity = 0
        self.color = (255, 0, 0)
        self.target_acquisition_ratio = 0
        self.on_target = False
    def draw(self, canvas):
        # draw rectangle
        pt1_x = int(np.round(self.pos_x - self.width//2))
        pt1_y = int(np.round(self.pos_y - self.height//2))
        pt1 = (pt1_x, pt1_y)
        pt2_x = int(np.round(self.pos_x + self.width//2))
        pt2_y = int(np.round(self.pos_y + self.height//2))
        pt2 = (pt2_x, pt2_y)
        cv2.rectangle(canvas, pt1, pt2, self.color, -1)

        # draw progress bar
        if self.target_acquisition_ratio > 0:
            pt3_x = int(np.round(pt1_x + self.width * self.target_acquisition_ratio))
            pt3_y = pt2_y 
            pt3 = (pt3_x, pt3_y)
            color = self.controller.target.color
            cv2.rectangle(canvas, pt1, pt3, color, -1)
        
        # add label
        text = 'Object'
        x = int(np.round(self.pos_x - 34))
        y = int(np.round(self.pos_y + 55))
        org = (x, y)
        fontface = cv2.FONT_HERSHEY_COMPLEX_SMALL
        cv2.putText(canvas, text, org, fontface, 1, self.color, 1, cv2.LINE_AA)

class Target:
    def __init__(self, radius, canvas_shape):
        self.radius = radius
        self.canvas_width = canvas_shape[1]
        self.canvas_height = canvas_shape[0]
        self.velocity = 10
        self.direction = 1
        self.randomize() 
    def randomize(self):
        r = random.randint(0,255)
        g = random.randint(0,255 - r)
        b = 255 - r - g
        self.color = (b, g, r)
        self.direction = [-1,1][random.randint(0,1)]
        self.pos_x = random.randint(50, self.canvas_width - 50)
        self.pos_y = 250
        # print(f'r: {r} | g: {g} | b: {b}')
    def draw(self, canvas):
        pos_x = int(np.round(self.pos_x))
        pos_y = int(np.round(self.pos_y))
        center = (pos_x, pos_y)
        if self.controller.rectangle.on_target:
            color = (255,255,255)
        else:
            color = self.color
        cv2.circle(canvas, center, self.radius, color, 2)

        # add label
        text = 'Target'
        x = int(np.round(self.pos_x - 34))
        y = int(np.round(self.pos_y - 38))
        org = (x, y)
        fontface = cv2.FONT_HERSHEY_COMPLEX_SMALL
        cv2.putText(canvas, text, org, fontface, 1, self.color, 1, cv2.LINE_AA)

    def move(self):
        if self.pos_x < 0:
            self.direction = 1
        elif self.pos_x > self.canvas_width:
            self.direction = -1
        self.pos_x += self.direction * self.velocity

class Controller:
    def __init__(self, rectangle, target, sample_time, kp=1, ki=.1, kd=.05):
        """
        A wrapper around simple_pid.PID
        """
        self.rectangle = rectangle
        self.target = target
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.pid = PID(kp, ki, kd, setpoint=target.pos_x) 
        self.pid.output_limits = (-20, 20) 
        # self.pid.sample_time = sample_time
        self.rectangle.controller = self
        self.target.controller = self
        self.target_acquisition_list = [False for n in range(40)]

    def apply_force(self, force):
        acceleration = force / self.rectangle.mass
        rectangle.velocity += acceleration
        rectangle.pos_x += rectangle.velocity 

    def check_target(self) -> bool:
        # check if the rectangle is on target
        if abs(self.rectangle.pos_x - self.target.pos_x) < self.rectangle.width/2:
            v = True
        else:
            v = False
        self.rectangle.on_target = v

        # update the list of recent target acquisition values
        self.target_acquisition_list.append(v)
        del self.target_acquisition_list[0]

        # update the rectangles' target_acquisition_ratio
        trues = 0 
        list_len = len(self.target_acquisition_list)
        for i in self.target_acquisition_list[::-1]:
            if i:
                trues += 1
            else:
                break
        target_acquisition_ratio = trues/list_len
        if target_acquisition_ratio < .1:
            target_acquisition_ratio = 0
        self.rectangle.target_acquisition_ratio = target_acquisition_ratio
        
        # determine if target has been consistently acquired and return that value
        if all(self.target_acquisition_list):
            return True
        else:
            return False

    def update_pid(self, input: float) -> float:
        output = self.pid(input)
        return output

    def update_setpoint(self, new_setpoint):
        self.pid.setpoint = new_setpoint

    def update_parameters(self, kpi: tuple) -> tuple:
        pass

    def draw(self):
        pass

# constants
FPS = 30
RESOLUTION = (500, 1000)
SAMPLE_TIME = 1 / FPS
WAIT_TIME = int(np.round(SAMPLE_TIME * 1000)) # milliseconds
WRITE_VIDEO = True

# globals
canvas = np.zeros([*RESOLUTION,3],dtype=np.uint8)
canvas.fill(255)
rectangle = Rectangle(10)
target = Target(10, canvas.shape)
kp = 1
ki = .05
kd = .5
controller = Controller(rectangle, target, SAMPLE_TIME, kp, ki, kd)

# initialize some values
force_direction = 1
force = 0
force_to_display = 0
interference_force = 0

# video writer
if WRITE_VIDEO:
    fourcc = cv2.VideoWriter_fourcc(*'h264') # supported by whatsapp
    filepath = 'output.mp4'
    writer = cv2.VideoWriter(filepath, fourcc, FPS, RESOLUTION[::-1])

n = 0 
t1 = timer()
while True:
    # copy the canvas so we have a clear one to draw on 
    canvas_copy = canvas.copy()

    # check target acquisition
    target_acquired = controller.check_target()
    if target_acquired:
        controller.target.randomize()
        controller.update_setpoint(target.pos_x)

    # # move target
    target.move()
    # print(controller.pid.setpoint)
    # controller.update_setpoint(controller.target.pos_x)

    # Compute new output from the PID according to the systems current value
    force = controller.update_pid(rectangle.pos_x - target.pos_x + controller.pid.setpoint)
    if n % int(FPS / 8) == 0:
        force_to_display = str(abs(np.round(force, decimals=2)))
        
        if force >= 0:
            s = '='
        else:
            s = '<'

        s += f'==={force_to_display}'

        for n in range(10 - len(s)):
            s += '='

        if force <= 0:
            s += '='
        else:
            s += '>'

        force_to_display = s

    # apply force
    force_to_apply = force + interference_force
    controller.apply_force(force_to_apply)   
    # print(f'force_to_apply: {force_to_apply} | force: {force} | interference_force: {interference_force}')
    interference_force = 0 # reset the interference

    # draw results
    rectangle.draw(canvas_copy)
    target.draw(canvas_copy)
    cv2.putText(canvas_copy, f"Kp: {kp}",(20,40),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,10,10),1,cv2.LINE_AA)
    cv2.putText(canvas_copy, f"Ki: {ki}",(20,80),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,10,10),1,cv2.LINE_AA)
    cv2.putText(canvas_copy, f"Kd: {kd}",(20,120),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,10,10),1,cv2.LINE_AA)
    cv2.putText(canvas_copy, f"Force: {force_to_display}",(20,160),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,10,10),1,cv2.LINE_AA)

    # record video
    if WRITE_VIDEO:
        writer.write(canvas_copy)

    # show results
    cv2.imshow('canvas_copy', canvas_copy)

    # check keys
    key = cv2.waitKey(WAIT_TIME)
    if key == ord('q'):
        break
    elif key == ord('a'):
        interference_force = -22
    elif key == ord('d'):
        interference_force = 22
    

    n += 1

t2 = timer()
elapsed_time = t2 - t1
print(f'elapsed_time: {elapsed_time}')
print(f'frames: {n}')
print(f'fps: {n / elapsed_time}')

if WRITE_VIDEO: 
    writer.release()

cv2.destroyAllWindows()
