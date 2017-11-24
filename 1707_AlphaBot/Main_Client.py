
import time
import Communication, Alphabot
from Utils import *


# Robot object
Ab = Alphabot.AlphaBot()

# Open communication channel
channel = Communication.ClientServerChannel('client')

# Main loop
try:
    target_period = 0.1  # target loop frequency: 10Hz
    last_tick = time.time()
    while not channel.is_closed():
        # Pause to match target frequency
        rem = last_tick + target_period - time.time()
        last_tick = time.time()
        if rem > 0:
            time.sleep(rem)
        else:
            print('Loop iteration took longer time than one target period, '
                  'consider increasing target_period')

        # Sensor input
        data = Ab.get_sensor_data()
        channel.send_sensor('IR', data)

        # Motor command
        name, motor = channel.read_motor()
        if name == 'motor':
            Ab.set_motor(motor[0], motor[1])
        else:
            print('no new motor command')

finally:
    channel.cleanup()
    Ab.cleanup()


print('done')
