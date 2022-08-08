from gpiozero import Button
import RPi.GPIO as GPIO
from threading import Thread
from multiprocessing import Process, Value
from time import sleep
from timeit import default_timer as timer
import numpy as np

class TransmitterButton:
    def __init__(self, pin, diagnostic_mode=True):
        self.position = Value('i', 0)
        
        self.pin = pin
        self.diagnostic_mode = diagnostic_mode
        
        self.THRESH1 = .075
        self.THRESH2 = .095
        
        # initialize GPIO pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

        # create some variables for checking if the position has changed
        self.previous_position = self.position.value

    def start(self):
        """
        Start the loop that listens to the button
        """

        # spawn the process
        self.p = Process(target=self.loop)
        self.p.start()

    def loop(self):
        """
        Continously check the button's status
        """
        self.recent_signals = [0 for n in range(500)]
        self.recent_counts = [0 for n in range(500)]
        self.average: float = 2
        
        # define some variables for diagnostic mode
        if self.diagnostic_mode:
            print('Starting TransmitterButton diagnostic mode...')
            self.graph_list = []
            t1 = timer()
            n = 0
        
        while True:
            # get the current signal
            current_signal = GPIO.input(self.pin)
            
            # count the positive signals in the list of n recent signals
            self.recent_signals.append(current_signal)
            del self.recent_signals[0]
            count = self.recent_signals.count(1) / len(self.recent_signals)
            
            # append the current count to a list of n recent counts
            self.recent_counts.append(count)
            self.recent_counts = self.recent_counts[1:]
            
            # find the average of the recent counts
            self.average = np.average(self.recent_counts)
            
            # set the switch position
            if 0 < self.average <= self.THRESH1:
                self.position.value = 0
            elif self.THRESH1 < self.average <= self.THRESH2:
                self.position.value = 1
            else:
                self.position.value = 2
                
            # if self.diagnostic_mode:
            if True:
                n += 1
                if n % 100 == 0:
                        self.graph_list.append(self.average)
                        
                if n > 100000:
                    t2 = timer()
                    elapsed_time = t2 - t1 # in seconds
                    freq = n / elapsed_time
                    print(f'Finished demonstration in {elapsed_time} seconds at {freq} hertz.')
                    
                    # graph the results
                    from matplotlib import pyplot
                    thresh1 = [self.THRESH1 for n in range(len(self.graph_list))]
                    thresh2 = [self.THRESH2 for n in range(len(self.graph_list))]
                    pyplot.plot(self.graph_list)
                    pyplot.plot(thresh1)
                    pyplot.plot(thresh2)
                    graphics_path = 'signal.png'
                    pyplot.savefig(graphics_path)
                    with open('signal.txt', 'w') as f:
                        for i in self.graph_list:
                            f.write(str(i) + ',')
                        f.write(f'\n{self.THRESH1}')
                        f.write(f'\n{self.THRESH2}')
                    print(f"All done! Results saved to {graphics_path}")
                    
                    # for demonstration purposes, break after a brief period of time
                    break
                
    def check_status(self) -> bool:
        """
        Checks if the button position differs from the last
        time it was checked
        """
        if self.previous_position != self.position.value:
            has_been_pressed = True
        else:
            has_been_pressed = False
        self.previous_position = self.position.value
        return has_been_pressed
        
    def release(self):
        """
        Terminate the loop that listens to the button
        """
        self.p.terminate()

class CustomButton:
    def __init__(self, pin):
        self.pin = pin
        self.run = False
        self.previous_position = 0
        self.current_position = 0
        self.has_been_pressed = False
        self.button = Button(self.pin)

    def start(self):
        def thread():
            self.run = True
            while self.run:
                self.previous_position = self.current_position
                if self.button.is_pressed:
                    self.current_position = 1
                else:
                    self.current_position = 0
                    
                if self.current_position == 0 and self.previous_position == 1:
                    self.has_been_pressed = True
                sleep(.1)
        Thread(target=thread).start()
        
    def check_status(self) -> bool:
        """
        Intended to be called by the main loop to check the status of the button.
        Returns a boolean indicating whether the button has been pressed.
        Sets button.has_been_pressed back to False.
        """
        if self.has_been_pressed == True:
            result = True
            self.has_been_pressed = False
        else:
            result = False
        return result
    
    def release(self):
        """
        Terminates the button's looping.
        """
        self.run = False
                
if __name__ == "__main__":
    transmitter_button = TransmitterButton(pin=22, diagnostic_mode=True)
    print('Starting demo...')
    transmitter_button.start()
    while True: # 15 seconds of demo
        sleep(.1)
        result = transmitter_button.check_status()
        if result:
            print('Button has been pressed!')
    
    transmitter_button.release()
    print('Demo finished!')