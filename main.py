import yaml
import json
from datetime import datetime
import time
from receiver import Receiver

from utils.messages import Message

# Read the configurations and convert to a Message object
path = "configurations.yaml"
with open(path, 'r') as f:
    config = Message(yaml.safe_load(f))

LOOP_DURATION = 1 / config.video.fps

# Initialize the receiver
receiver = Receiver(config.receiver)
# TODO implement proper logging
print('Connecting to receiver...')
receiver.connect()
print('Connected to receiver!')

# Initialize the flight controller

# Initialize the camera

# Initialize the switch positions to 0. We will keep track of when
# they change position. 0 is considered the "off" or safe position.
autopilot_switch_pos = 0
recording_switch_pos = 0

t1 = time.time() # Initialize the FPS timer
while True:
    # Get the parsed SBUS packet (None -> ParsedPacket)
    packet = receiver.get_parsed_packet()
    print(packet)

    # Get a frame from the camera (None -> frame)

    # Perform horizon detection (frame -> Attitude/Horizon)

    # Run flight_controller (SensorMesssage, ParsedPacket -> None)

    # Handle recording (ParsedPacket[recording_switch] -> None)
    if packet.switches.rec == 1 and recording_switch_pos != 0:
        pass

    # Start recording
    if 'recording_switch_pressed':
        # Get the current time
        current_time = datetime.now()
        time_string = current_time.strftime('%Y-%m-%d %H:%M:%S')
        diagnostic_data = {
            'metadata': {
                'config': config.data,
                'time': time_string,
            }
        }
        
    # Stop recording
    if 'recording_switch_released':
        pass

    # Wait a variable amount to maintain FPS
    time_elapsed_so_far = time.time() - t1
    addl_time_to_wait = LOOP_DURATION - time_elapsed_so_far
    if addl_time_to_wait > 0:
        time.sleep(addl_time_to_wait)

    # Measure the FPS
    t2 = time.time()
    # print(f'fps: {1 / (t2 - t1)}')
    
    # Restart the FPS timer
    t1 = t2