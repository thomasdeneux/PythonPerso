import random
import time
import numpy as np

import Communication

_target_period = 0.01  # data is sent at 100Hz


# noinspection PyMethodMayBeStatic
class ClientServerChannel:

    def __init__(self):
        self.last_tick = time.time()
        self.current_motor = [0, 0]

    def read_sensor(self):
        # Wait for next 'available data'
        time.sleep(self.last_tick + _target_period - self.last_tick)
        self.last_tick = time.time()

        # Fake data
        name = 'IR'
        data = Communication.SensorData()
        data.IR_left = random.uniform(0., 1000.)
        data.IR_right = random.uniform(0., 1000.)
        data.IR_line = [random.uniform(0., 1000.) for i in range(5)]
        data.speed = np.maximum(np.array(self.current_motor)-10, 0).tolist()
        return name, data

    def send_motor(self, name, data):
        self.current_motor = data
        pass

    def is_closed(self):
        return False

    def cleanup(self):
        pass