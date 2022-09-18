import os
from time import sleep
from switches_and_servos import ServoHandler

def update(update_path):
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
    
    # check if the file is a python file
    updated_files = 0
    for i in os.listdir(update_path):
        if i.split('.')[-1] not in ['py', 'txt']:
            continue
        
        # do not update the autoupdater file
        if i == 'autoupdater.py':
            continue
        
        # check if the file exists in the current code base
        current_path = '/home/pi/horizon_detector'
        if i not in os.listdir(current_path):
            continue
        
        # check if there have been any updates to the file
        with open(f'{update_path}/{i}') as f:
            text_in_update_file = f.read()
        with open(f'{current_path}/{i}') as f: 
            text_in_current_file = f.read()
        if text_in_update_file == text_in_current_file:
            continue
        
        # write the new values to the code base
        with open(f'{current_path}/{i}', 'w') as f:
            f.write(text_in_update_file)
        
        updated_files += 1
        
    print(f'{updated_files} files updated.')
    if updated_files > 0:
        ail_handler = ServoHandler(13, 12, 30, 990, 2013)
        for n in range(updated_files):
            sleep(.5)
            ail_handler.actuate(.5)
            sleep(.5)
            ail_handler.actuate(0)
        sleep(2)           
    
if __name__ == "__main__":
    path = '/media/pi/scratch/update_package'
    update(path)