import random
import subprocess
import time
import os

import Communication
import FakeRobot
from Utils import *
import AlphaI

# RobotIP = '157.136.60.136'
# RobotIP = '10.0.0.1'
# RobotIP = None
RobotIP = '192.168.50.5'


def start_remote_client(fake=True):
    if RobotIP is None:
        # Robot is out of reach, use a fake robot instead
        chan = FakeRobot.ClientServerChannel()
    else:
        # # Copy Python files to the Raspberry
        # print('Copy Python files to the Raspberry')
        # if os.name == 'nt':
        #     subprocess.call(['pscp', '*.py', 'Run_Client.txt',
        #                      'pi@' + RobotIP + ':Python/PythonPerso/1707_AlphaBot'])
        # elif os.name == 'posix':
        #     os.system('scp *.py Run_Client.txt pi@10.0.0.1:Python/PythonPerso/1707_AlphaBot')

        # # Execute client code on the raspberry
        # print('Start the remote client')
        # if os.name == 'nt':
        #     subprocess.Popen(
        #         ['putty', '-ssh', 'pi@' + RobotIP, '-m', 'Run_Client.txt', '-t'])
        # elif os.name == 'posix':
        #     subprocess.Popen(
        #         ['ssh', 'pi@' + RobotIP, 'python3 Python/PythonPerso/1707_AlphaBot/Main_Client.py'])

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
