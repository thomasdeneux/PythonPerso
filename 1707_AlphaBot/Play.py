from gpiozero import Button, Robot
from time import time, sleep
from math import floor

import RPi.GPIO as GPIO
import time
from AlphaBot import AlphaBot

Ab = AlphaBot()

IN1 = 2
IN2 = 3
IN3 = 20
IN4 = 21
DL = 19
DR = 16
SDL = 7
SDR = 8

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(DR,GPIO.IN,GPIO.PUD_UP)
GPIO.setup(DL,GPIO.IN,GPIO.PUD_UP)


class SpeedDetector(Button):

    def __init__(self, pin, integrate_time=.1):
        super(SpeedDetector, self).__init__(pin=pin)
        self.when_pressed = self.motion_event
        self.when_released = self.motion_event
        self.integrate_time = integrate_time
        self.current_speed = 0.
        self.count_start_time = time()
        self.count = 0

    def update_speed(self):
        # if a counting interval finished, update current speed and start a
        # new one
        t = time()
        if t - self.count_start_time > self.integrate_time:
            if t - self.count_start_time > 2*self.integrate_time:
                self.current_speed = 0.
            else:
                self.current_speed = self.count / self.integrate_time
            self.count_start_time = self.count_start_time + floor(t - self.count_start_time)
            self.count = 0

    def motion_event(self):
        self.update_speed()
        self.count += 1

    def get_speed(self):
        self.update_speed()
        return self.current_speed


# Go!
a = SpeedDetector(SDL)
print(a.get_speed())
sleep(.2)
print(a.get_speed())
sleep(.2)
print('forward')
Ab.forward()
sleep(.2)
print(a.get_speed())
sleep(.2)
print(a.get_speed())
sleep(.2)
print(a.get_speed())
sleep(.2)
print(a.get_speed())
sleep(.2)
print('stop')
Ab.stop()

# try:
#     while True:
#         DR_status = GPIO.input(DR)
#         DL_status = GPIO.input(DL)
#         if((DL_status == 1) and (DR_status == 1)):
#             Ab.forward()
#             print("forward")
#         elif((DL_status == 1) and (DR_status == 0)):
#             Ab.left()
#             print("left")
#         elif((DL_status == 0) and (DR_status == 1)):
#             Ab.right()
#             print("right")
#         else:
#             Ab.backward()
#             time.sleep(0.2)
#             Ab.left()
#             time.sleep(0.2)
#             Ab.stop()
#             print("backward")
#
# except KeyboardInterrupt:
#     GPIO.cleanup();
