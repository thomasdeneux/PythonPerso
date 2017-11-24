import random
import subprocess
import time

import Communication
import FakeRobot
from Utils import *
import AlphaI

# RobotIP = '157.136.60.136'
RobotIP = '10.0.0.1'
# RobotIP = None


def start_remote_client(fake=True):
    if RobotIP is None:
        # Robot is out of reach, use a fake robot instead
        chan = FakeRobot.ClientServerChannel()
    else:
        # Copy Python files to the Raspberry
        print('Copy Python files to the Raspberry')
        subprocess.call(['pscp', '*.py', 'Run_Client.txt',
                         'pi@' + RobotIP + ':Python/PythonPerso/1707_AlphaBot'])

        # Execute client code on the raspberry
        print('Start the remote client')
        subprocess.Popen(
            ['putty', '-ssh', 'pi@' + RobotIP, '-m', 'Run_Client.txt', '-t'])

        # Open communication channel
        time.sleep(1)  # wait a second to make sure client is ready
        chan = Communication.ClientServerChannel('server', RobotIP)

    return chan


# Start remote client
channel = start_remote_client()

# Run AI
AlphaI.AI(channel)

# Clean channel
channel.cleanup()

print('done')
