import cv2
import numpy as np
from matplotlib import pyplot
from draw_display import draw_horizon

class FlightController:
    def __init__(self):
        self.previous_angle = 0
        self.loops = 0

    def convert_angle(self, angle: float) -> float:
        lower = angle + (self.loops - 1) * 360
        same = angle + self.loops * 360
        higher = angle + (self.loops + 1) * 360

        same_diff = abs(same - self.previous_angle)
        lower_diff = abs(lower - self.previous_angle)
        higher_diff = abs(higher - self.previous_angle)

        min_val = min([same_diff, lower_diff, higher_diff])

        if min_val == same_diff:
            return_angle = same
        elif min_val == higher_diff:
            return_angle = higher
            self.loops += 1
        else:
            return_angle = lower
            self.loops -= 1        
        
        self.previous_angle = return_angle
        return return_angle

canvas = np.zeros((500, 1000, 3), dtype = "uint8")
flight_controller = FlightController()

autopilot = False

# initialize angle-related variabls
UPPER_RANGE = 360
angle = 0
previous_angle = 0
angular_velocity = .1
MAX_ANGULAR_VELOCITY = 3
increment = .33

# lists for graphing
angle_list = []
return_angle_list = []

n = 0
while True:
    # increment the angle
    new_angle = previous_angle + angular_velocity
    if new_angle >= UPPER_RANGE:
        angle = new_angle - UPPER_RANGE
    elif new_angle < 0:
        angle = new_angle + UPPER_RANGE
    else:
        angle = new_angle
    previous_angle = angle

    # adjust the angle
    if autopilot:
        return_angle = flight_controller.convert_angle(angle)
    else:
        return_angle = None

    # record results
    angle_list.append(angle)
    return_angle_list.append(return_angle)

    # modulate the pitch

    # draw
    canvas_copy = canvas.copy()
    normalized_angle = angle/360
    try:
        draw_horizon(canvas_copy, normalized_angle, .5, 0, True, (100, 100))
    except:
        print('Exception!')

    angle_to_draw = int(np.round(angle))
    if return_angle:
        return_angle_to_draw = int(np.round(return_angle))
    else:
        return_angle_to_draw = ''

    cv2.putText(canvas_copy, f"angle: {angle_to_draw}",(20,40),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,200,200),1,cv2.LINE_AA)
    cv2.putText(canvas_copy, f"return_angle: {return_angle_to_draw}",(20,80),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(200,200,200),1,cv2.LINE_AA)

    # show canvas
    cv2.imshow('canvas_copy', canvas_copy)

    # check keys
    key = cv2.waitKey(10)
    if key == ord('q'):
        break
    elif key == ord('1'):
        angular_velocity -= increment
    elif key == ord('2'):
        angular_velocity += increment
    elif key == ord('a'):
        autopilot = not autopilot
        print(f'autopilot: {autopilot}')

        # reinitialize the flight controller
        if autopilot:
            flight_controller = FlightController()

    # adjust the angular velocity within the range of accepted values
    if angular_velocity > MAX_ANGULAR_VELOCITY:
        angular_velocity = MAX_ANGULAR_VELOCITY
    elif angular_velocity < -1 * MAX_ANGULAR_VELOCITY:
        angular_velocity = -1 * MAX_ANGULAR_VELOCITY

    n += 1     

# save the graph
pyplot.plot(angle_list)
pyplot.plot(return_angle_list)
graphics_path = 'results.png'
pyplot.savefig(graphics_path)
print(f"All done! Results saved to {graphics_path}")  

# show the graph
results = cv2.imread('results.png')
cv2.imshow('results', results)
cv2.waitKey(0)

# destroy all windows
cv2.destroyAllWindows()



        
