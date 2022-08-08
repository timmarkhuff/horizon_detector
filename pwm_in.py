import RPi.GPIO as GPIO
from threading import Thread
from multiprocessing import Process
from time import sleep
import numpy as np
from timeit import default_timer as timer

import global_variables as gv
        
class AutoPilotSwitch:
    def __init__(self, pin, diagnostic_mode=False):
        self.pin = pin
        self.diagnostic_mode = diagnostic_mode
        self.recent_signals = [0 for n in range(400)]
        self.recent_counts = [0 for n in range(400)]
        self.average: float = 2
        self.position = 2
        self.run = True
        
        self.THRESH1 = .075
        self.THRESH2 = .095
        
        # initialize GPIO pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        
    def listen(self):
        def thread():
            
            # define some variables for diagnostic mode
            if self.diagnostic_mode:
                self.graph_list = []
                t1 = timer()
                n = 0
            
            # start the listening loop
            self.run = True
            while self.run:
                # get the current signal
                current_signal = GPIO.input(self.pin)
                
                # count the positive signals in the list of n recent signals
                self.recent_signals.append(current_signal)
                self.recent_signals = self.recent_signals[1:]
                count = self.recent_signals.count(1) / len(self.recent_signals)
                
                # append the current count to a list of n recent counts
                self.recent_counts.append(count)
                self.recent_counts = self.recent_counts[1:]
                
                # find the average of the recent counts
                self.average = np.average(self.recent_counts)
                
                # set the switch position
                if 0 < self.average <= self.THRESH1:
                    self.position = 0
                elif self.THRESH1 < self.average <= self.THRESH2:
                    self.position = 1
                else:
                    self.position = 2
                
                if self.position == 2:
                    gv.autopilot = True
                else:
                    gv.autopilot = False
                
                # diagnostic mode only
                if self.diagnostic_mode:
                    n += 1
                    if n % 100 == 0:
                        self.graph_list.append(self.average)

                        
                    if n > 50000:
                        t2 = timer()
                        elapsed_time = t2 - t1 # in seconds
                        freq = n / elapsed_time
                        print(f'Finished demonstration in {elapsed_time} seconds at {freq} hertz.')
                        
                        # for demonstration purposes, break after a brief period of time
                        break
                    
#                 # wait 
#                 sleep(.00001)
            
            self.run = False           
            
        Process(target=thread).start()
    
    def release(self):
        self.run = False        

if __name__ == "__main__":
    from matplotlib import pyplot
    autopilotswitch = AutoPilotSwitch(22, True)
    autopilotswitch.listen()
    print('Listening to switch input...')
    
    while autopilotswitch.run:
        sleep(1)
    
    thresh1 = [autopilotswitch.THRESH1 for n in range(len(autopilotswitch.graph_list))]
    thresh2 = [autopilotswitch.THRESH2 for n in range(len(autopilotswitch.graph_list))]
    pyplot.plot(autopilotswitch.graph_list)
    pyplot.plot(thresh1)
    pyplot.plot(thresh2)
    graphics_path = 'signal.png'
    pyplot.savefig(graphics_path)
    print(f"All done! Results saved to {graphics_path}")
    
        
        

        
        