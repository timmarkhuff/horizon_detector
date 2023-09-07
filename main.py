import yaml
import os
import json
from datetime import datetime
import time
from receiver import Receiver

from utils import Message, save_json_in_thread
from flight_controller import FlightController, ManualFlightProgram, SurfaceCheckProgram, QuickWiggleProgram
from video import CameraCapture, VideoRecorder

from horizon_detector import HorizonDetector, get_cropping_and_scaling_parameters, crop_and_scale

def main():
    # Read the configurations and convert to a Message object
    path = "configurations.yaml"
    with open(path, 'r') as f:
        config = Message(yaml.safe_load(f))

    FPS = config.video.fps
    LOOP_DURATION = 1 / FPS
    RECORDINGS_FOLDER_PATH = 'recordings'
    CAPTURE_WIDTH = config.video.resolution.capture.width
    CAPTURE_HEIGHT = config.video.resolution.capture.height

    # Make a folder for the recordings if there isn't one already
    if not (os.path.exists(RECORDINGS_FOLDER_PATH) and os.path.isdir(RECORDINGS_FOLDER_PATH)):
        os.mkdir(RECORDINGS_FOLDER_PATH)

    # Initialize the receiver
    receiver = Receiver(config.receiver)
    print('Connecting to receiver...')
    receiver.connect()
    initialization_packet = receiver.get_parsed_packet()
    print('Connected to receiver!')

    # Initialize the horizon detector
    INFERENCE_RESOLUTION = (100, 100)
    RESOLUTION = frame.shape[1::-1] # extract the resolution from the frame
    CROP_AND_SCALE_PARAM = get_cropping_and_scaling_parameters(RESOLUTION, INFERENCE_RESOLUTION)
    EXCLUSION_THRESH = 5 # degrees of pitch above and below the horizon
    FOV = 48.8
    ACCEPTABLE_VARIANCE = 1.3 
    horizon_detector = HorizonDetector(EXCLUSION_THRESH, FOV, ACCEPTABLE_VARIANCE, INFERENCE_RESOLUTION)

    # Initialize the flight controller
    flight_controller = FlightController(config.flight_controller)

    # Initialize the camera
    camera_capture = CameraCapture(0, CAPTURE_WIDTH, CAPTURE_HEIGHT)

    # Initialize the switch positions to 0. We will keep track of when
    # they change position. 0 is considered the "off" or safe position.
    prev_recording_switch_pos = initialization_packet.switches.rec
    prev_autopilot_switch_pos = initialization_packet.switches.auto
    recording = False

    actual_fps = config.video.fps

    t1 = time.time() # Initialize the FPS timer
    while True:
        # Get the parsed SBUS packet (None -> ParsedPacket)
        packet = receiver.get_parsed_packet()
        # print(packet)

        frame = camera_capture.read()

        frame_small = crop_and_scale(frame, **CROP_AND_SCALE_PARAM)
        output = horizon_detector.find_horizon(frame_small, diagnostic_mode=False)
        print(output)

        # Perform horizon detection (frame -> Attitude/Horizon)
        sensor_msg = Message()

        # Run flight_controller (SensorMesssage, ParsedPacket -> Flight Controller Output)
        flt_ctrlr_output = flight_controller.run(packet, sensor_msg)
        # print(flt_ctrlr_output)

        # Monitor changes in switch positions and trigger events accordingly
        # Start recording
        if packet.switches.rec == 1 and prev_recording_switch_pos != 1:
            print('Starting recording!')
            recording = True
            flight_controller.flight_program = SurfaceCheckProgram()

            current_time = datetime.now()
            recording_start_time_string = current_time.strftime('%Y-%m-%d %H:%M:%S')

            video_filepath = f'{RECORDINGS_FOLDER_PATH}/{recording_start_time_string}.avi'
            video_recorder = VideoRecorder(video_filepath, CAPTURE_WIDTH, CAPTURE_HEIGHT, FPS)

            diagnostic_data = {
                'metadata': {
                    'config': config.data,
                    'time': recording_start_time_string,
                },
                'frames': []
            }
        # Stop recording
        elif recording and packet.switches.rec != 1 and prev_recording_switch_pos == 1:
            print('Stopping recording!')
            recording = False
            flight_controller.flight_program = QuickWiggleProgram()

            json_filepath = f'{RECORDINGS_FOLDER_PATH}/{recording_start_time_string}.json'
            save_json_in_thread(json_filepath, diagnostic_data)

            video_recorder.release()

        # Activate autopilot
        if packet.switches.auto == 1 and prev_autopilot_switch_pos != 1:
            flight_controller.flight_program = SurfaceCheckProgram()
        # Activate manual flight
        elif packet.switches.auto != 1 and prev_autopilot_switch_pos == 1:
            flight_controller.flight_program = ManualFlightProgram()

        # Handle recording (ParsedPacket[recording_switch] -> None)
        if recording:
            frame_data = {
                'fps': actual_fps,
                'packet': packet.data,
                'flt_ctrlr_output': flt_ctrlr_output.data,
                # 'sensor': sensor_msg.data,
            }
            diagnostic_data['frames'].append(frame_data)

            video_recorder.put_in_queue(frame)

        # Remember the previous switch positions so we can monitor for changes in position
        # in the next iteration
        prev_recording_switch_pos = packet.switches.rec
        prev_autopilot_switch_pos = packet.switches.auto

        # Wait a variable amount to maintain steady FPS
        time_elapsed_so_far = time.time() - t1
        addl_time_to_wait = LOOP_DURATION - time_elapsed_so_far
        if addl_time_to_wait > 0:
            time.sleep(addl_time_to_wait)

        # Measure the FPS
        t2 = time.time()
        actual_fps = 1 / (t2 - t1)
        
        # Restart the FPS timer
        t1 = t2


if __name__ == "__main__":
    main()
    # try:
    #     main()
    # except KeyboardInterrupt as e:
    #     print(e)
    # finally:
    #     camera_capture.release()
    #     video_recorder.release()
    #     print('Resources released!')