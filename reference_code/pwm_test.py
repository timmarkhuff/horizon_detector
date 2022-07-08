import pigpio
from time import sleep

gpio_in = pigpio.pi()
gpio_out = pigpio.pi()
sleep(1)

while True:
    input_value = gpio_in.read(17)
    gpio_out.write(27, input_value)