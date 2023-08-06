import os
from time import sleep

def disable_wifi_and_bluetooth():
    # Block WIFI and Bluetooth
    os.system('sudo rfkill block wifi')
    os.system('sudo rfkill block bluetooth')
    
    # Check status of WIFI and Bluetooth
    print_out = os.popen('sudo rfkill list').read()

    print_out_cleaned = ''
    for i in print_out:
        if ord(i) == 10:
            print_out_cleaned += ' '
        elif ord(i) == 9:
            print_out_cleaned += ''
        else:
            print_out_cleaned += i
                    
    print(f'Status print out: {print_out_cleaned}')

    # Report WIFI Status
    if "Wireless LAN Soft blocked: yes" in print_out_cleaned:
        wifi_response = "Wifi Disabled."
    elif "Wireless LAN Soft blocked: no":
        wifi_response = "Warning! Wifi is still enabled."
    else:
        wifi_response = "Warning! Wifi status could not be determined."

    # Report Bluetooth Status
    if "Bluetooth Soft blocked: yes" in print_out_cleaned:
        bluetooth_response = "Bluetooth Disabled."
    elif "Bluetooth Soft blocked: no":
        bluetooth_response = "Warning! Bluetooth is still enabled."
    else:
        bluetooth_response = "Warning! Bluetooth status could not be determined."
    
    return wifi_response, bluetooth_response
    
if __name__ == "__main__":
    from text_to_speech import speaker
    wifi_response, bluetooth_response = disable_wifi_and_bluetooth()
    speaker.add_to_queue(f'{wifi_response} {bluetooth_response}')
    sleep(1) # wait for speaker to get started
    
    # wait for the speaker to finish
    for n in range(200):
        if speaker.isSpeaking:
            sleep(.01)
        else:
            break
                
    speaker.release()
    print('Ending demo.')
    
    
    
    
    
    