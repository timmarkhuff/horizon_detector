from time import sleep
from switches_and_servos import TrimReader

pitch_trim_reader = TrimReader(input_pin=25)

while True:
    sleep(.5)
    pitch_trim = pitch_trim_reader.read()
    print(pitch_trim)
    
    