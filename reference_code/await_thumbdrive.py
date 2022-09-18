import os
from time import sleep
from switches_and_servos import ServoHandler

def await_thumbdrive(update_path):
    # check if path exists
    timeout = 60
    for n in range(timeout):
        if os.path.exists(update_path):
            break
        else:
            sleep(1)
    else: 
        print('No update directory found. Please check that you have plugged in the thumbdrive.')
        return
       
if __name__ == "__main__":
    path = '/media/pi/scratch'
    await_thumbdrive(path)