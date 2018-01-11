
import time
import Communication, AlphaBot
from Utils import *

# Robot object
Ab = AlphaBot.AlphaBot()kkkk

# Open communication channel
channel = Communication.ClientServerChannel('client', interrupt_action=Ab.stop)

# Main loop
try:
    target_period = 0.25  # target loop frequency: 10Hz
    last_tick = time.time()
    while not channel.is_closed():
        # Pause to match target frequency
        step_duration = time.time() - last_tick
        if step_duration < target_period:
            print('step duration (s):', step_duration, '-> sleeping')
            time.sleep(target_period-step_duration)
        else:
            print('step duration (s):', step_duration)
        last_tick = time.time()

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
