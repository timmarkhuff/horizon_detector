from gpiozero import Button, LED
from threading import Thread
from time import sleep

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
    button = CustomButton(pin=17)
    print('Starting demo...')
    button.start()
    for n in range(150): # 15 seconds of demo
        sleep(.1)
        result = button.check_status()
        if result:
            print('Button has been pressed!')
    
    button.release()
    print('Demo finished!')
        
        
        
        
        
        