import numpy as np
import random

from Utils import *
import Communication
import GUI

history_length = 200
DO_GUI = True
max_speed = 50.


class AI:

    def __init__(self, channel: Communication.ClientServerChannel):
        # Channel
        self.channel = channel

        # Current values
        self.sensor = None          # type: Communication.SensorData
        self.motor = np.zeros(2)    # current motor

        # History
        self.sensor_history = Communication.SensorData()    # sensor history
        self.sensor_history.IR_left = np.zeros(history_length)
        self.sensor_history.IR_right = np.zeros(history_length)
        self.sensor_history.IR_line = np.zeros((history_length, 5))
        self.sensor_history.speed = np.zeros((history_length, 2))
        self.motor_history = np.zeros((history_length, 2))  # motor history

        # Display
        if DO_GUI:
            self.gui = GUI.Display(self)

        # Go!
        try:
            self.main_loop()
        finally:
            self.channel.cleanup()

    # Main loop
    def main_loop(self):

        # Note that it is the client side that sets the loop frequency
        while not self.channel.is_closed():
            # Sensor input
            name, data = self.channel.read_sensor()
            if name != 'IR':
                raise Exception('no sensor data')
            self.sensor = data

            # Motor command: Brownian motion!
            decay = 0
            noise = 5
            self.motor[0] = max(-max_speed,
                                min(max_speed, self.motor[0] * (1. - decay)
                                    + random.uniform(-1., 1.) * noise))
            self.motor[1] = max(-max_speed,
                                min(max_speed,
                                    self.motor[1] * (1. - decay)
                                    + random.uniform(-1., 1.) * noise))
            self.channel.send_motor('motor', self.motor)

            # Update history
            hist = self.sensor_history
            hist.IR_left[:-1] = hist.IR_left[1:]
            hist.IR_left[-1] = data.IR_left
            hist.IR_right[:-1] = hist.IR_right[1:]
            hist.IR_right[-1] = data.IR_right
            hist.IR_line[:-1, ...] = hist.IR_line[1:, ...]
            hist.IR_line[-1, ...] = data.IR_line
            hist.speed[:-1, ...] = hist.speed[1:, ...]
            hist.speed[-1, ...] = data.speed
            self.motor_history[:-1, ...] = self.motor_history[1:, ...]
            self.motor_history[-1, ...] = self.motor

            # Update display
            if DO_GUI:
                self.gui.update()



