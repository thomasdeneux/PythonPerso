import RPi.GPIO as GPIO
import gpiozero
import Communication
import time
import numpy as np
from math import floor
from collections import deque

_speed_buffer_size = 8
_speed_integrate_time = .5


# noinspection PyPep8Naming
class AlphaBot:

    # Constructor
    def __init__(self):
        print('Init AlphaBot')

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # SENSORS

        # A/D conversion
        self.CS = 5
        self.Clock = 25
        self.Address = 24
        self.DataOut = 23
        GPIO.setup(self.Clock, GPIO.OUT)
        GPIO.setup(self.Address, GPIO.OUT)
        GPIO.setup(self.CS, GPIO.OUT)
        GPIO.setup(self.DataOut, GPIO.IN, GPIO.PUD_UP)

        # Front infra-red sensors
        # self.DR, self.DL = 16, 19  # digital
        # GPIO.setup(self.DL, GPIO.IN, GPIO.PUD_UP)
        # GPIO.setup(self.DR, GPIO.IN, GPIO.PUD_UP)
        self.TAL, self.TAR = 8, 9  # analog (addresses for A/D conversion)

        # Line-tracking infrared sensors
        self.TIR = list(range(0, 5))

        # # Speed detection
        self.SDL, self.SDR = 7, 8
        self.speed_buttons = [gpiozero.Button(self.SDL, pull_up=True),
                              gpiozero.Button(self.SDR, pull_up=True)]
        # if i use a loop instead of the 2 lines below, both function will
        # have argument 1, instead of 0 and 1!! is this a bug?
        self.speed_buttons[0].when_pressed = lambda: self.motion_event(0)
        self.speed_buttons[1].when_pressed = lambda: self.motion_event(1)
        self.speed_events = (deque(maxlen=_speed_buffer_size),
                             deque(maxlen=_speed_buffer_size))

        # MOTOR
        self.IN1, self.IN2, self.ENA = 12, 13, 6
        self.IN3, self.IN4, self.ENB = 20, 21, 26
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        GPIO.setup(self.IN3, GPIO.OUT)
        GPIO.setup(self.IN4, GPIO.OUT)
        GPIO.setup(self.ENA, GPIO.OUT)
        GPIO.setup(self.ENB, GPIO.OUT)
        self.stop()
        self.PWMA = GPIO.PWM(self.ENA, 500)
        self.PWMB = GPIO.PWM(self.ENB, 500)
        self.PWMA.start(50)
        self.PWMB.start(50)

    def cleanup(self):
        self.stop()

    # Sensor methods
    def get_sensor_data(self):
        s = Communication.SensorData()
        # Read all analog data at once
        x = self._get_analog_data([self.TAL, self.TAR]+self.TIR)
        s.IR_right = x[0]
        s.IR_left = x[1]
        s.IR_line = x[2:7]
        # Speed
        s.speed = self.get_speed()
        return s

    def get_digital_IR(self):
        return GPIO.input(self.DL), GPIO.input(self.DR)

    def _get_analog_data(self, addresses: list, nrepeat=1):

        DEBUG = False
        if DEBUG:
            bits = [0] * 10

        # Prepare container for values
        naddress = len(addresses)
        values = np.zeros(naddress*nrepeat, 'uint16')

        # Prepare list of addresses to ask conversion for
        addresses = np.array(addresses).repeat(nrepeat)

        # Enable TCL1543 board -> start sampling out current value on DATAOUT
        GPIO.output(self.CS, GPIO.LOW)
        # time.sleep(2e-7)  # setup time: 100ns

        # Loop: one more loop repeat because the address set at loop k is
        # sampled at loop (k+1)
        for k_addr in range(naddress*nrepeat+1):
            if k_addr < naddress*nrepeat:
                address = addresses[k_addr]
                if DEBUG:
                    print('address', address, ':', end='')


            # Sample 10 bits value and set address for next time
            for i in range(10):
                # Collect the currently sampled bit
                if k_addr:
                    values[k_addr-1] <<= 1
                    if GPIO.input(self.DataOut):
                        values[k_addr-1] |= 0x01
                if DEBUG:
                    bits[i] = GPIO.input(self.DataOut)

                # Set address
                if i < 4:
                    # noinspection PyUnboundLocalVariable
                    if (address >> (3-i)) & 0x01:
                        GPIO.output(self.Address, GPIO.HIGH)
                    else:
                        GPIO.output(self.Address, GPIO.LOW)

                # Trigger reading the address bit from ADDRESS
                GPIO.output(self.Clock, GPIO.HIGH)
                # time.sleep(250e-9)  # min pulse dur 190ns, max freq 2.1MHz

                # Trigger shift to the next bit on DATAOUT
                GPIO.output(self.Clock, GPIO.LOW)
                # time.sleep(250e-9)  # min pulse dur 190ns, max freq 2.1MHz

            # Wait to ensure conversion finished (takes 9.5us)
            time.sleep(10e-6)

            if DEBUG:
                print(''.join([str(x) for x in bits]))

        # Disable TCL1543 board
        GPIO.output(self.CS, GPIO.HIGH)

        # Output
        if nrepeat > 1:
            # Average over repeats
            values = values.reshape((naddress, nrepeat))
            values = values.mean(axis=1, dtype='float')
        return values

    def motion_event(self, side):
        self.speed_events[side].append(time.time())

    def get_speed(self):
        speed = [0]*2
        for i in range(2):
            q = np.array(self.speed_events[i])
            q = q[time.time() - q < _speed_integrate_time]
            if len(q) < 2:
                # less than 2 recent events, robot is not moving
                speed[i] = 0
            else:
                speed[i] = (len(q) - 1) / (q[-1] - q[0])  # unit: events/second
        return speed

    def is_moving(self):
        return self.get_speed() > 0

    # Motor methods
    def forward(self):
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.HIGH)

    def stop(self):
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.LOW)

    def backward(self):
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.HIGH)
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)

    def left(self):
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.HIGH)

    def right(self):
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.LOW)

    def setPWMA(self, value):
        self.PWMA.ChangeDutyCycle(value)

    def setPWMB(self, value):
        self.PWMB.ChangeDutyCycle(value)

    def set_motor(self, left, right):
        # Set left motor (beware, forward left wheel motion makes the robot
        # turn right)
        if (left >= 0) and (left <= 100):
            GPIO.output(self.IN1, GPIO.HIGH)
            GPIO.output(self.IN2, GPIO.LOW)
            self.PWMA.ChangeDutyCycle(left)
        elif (left < 0) and (left >= -100):
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.HIGH)
            self.PWMA.ChangeDutyCycle(0 - left)
        # Set right motor (and vice-versa...)
        if (right >= 0) and (right <= 100):
            GPIO.output(self.IN3, GPIO.HIGH)
            GPIO.output(self.IN4, GPIO.LOW)
            self.PWMB.ChangeDutyCycle(right)
        elif (right < 0) and (right >= -100):
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.HIGH)
            self.PWMB.ChangeDutyCycle(0 - right)


