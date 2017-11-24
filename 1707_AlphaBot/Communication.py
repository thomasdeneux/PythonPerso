import socket, struct, pickle
import numpy as np


_SensorPort = 50030
_MotorPort = 50031


class SensorData:
    def __init__(self):
        self.IR_left = None   # digital for the moment (later will be analog)
        self.IR_right = None
        self.IR_line = None   # type: list
        self.speed = None     # type: list


# The channel between client (robot) and server (PC running IA) will
# consists of two sockets, one for each direction. Clearly the robot to PC
# socket will transfer more data (sensor data) than the PC to robot socket (
# motor commands)
class ClientServerChannel:

    def __init__(self, side, robot_ip='10.0.0.1'):
        # are we on the server or client side?
        self.side = side
        if side == 'server':
            self.is_server = True
        elif side == 'client':
            self.is_server = False
        else:
            raise Exception("side argument must be either 'server' or "
                            "'client'")

        # hand checking: it is actually the server that tries to connect the
        # client, because only the robot has a fix IP address...
        print('Hand checking (' + self.side + ' side)', end='')
        if self.is_server:
            # sensor stream
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((robot_ip, _SensorPort))
            self.sensor_socket = s
            self.sensor_file = s.makefile('rb')
            # motor stream
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((robot_ip, _MotorPort))
            self.motor_socket = s
            self.motor_file = s.makefile('wb')
        else:
            # sensor stream
            s0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s0.bind(('', _SensorPort))
            s0.listen(1)
            self.sensor_socket, address = s0.accept()
            s0.close()
            self.sensor_file = self.sensor_socket.makefile('wb')
            # motor stream
            s0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s0.bind(('', _MotorPort))
            s0.listen(1)
            self.motor_socket, address = s0.accept()
            s0.close()
            self.motor_file = self.motor_socket.makefile('rb')
        print(' [done]')

    def cleanup(self):
        print('Cleaning up communication channel (' + self.side + ' side)')
        self.sensor_socket.close()
        self.sensor_file.close()

    def is_closed(self):
        return self.sensor_file.closed or self.motor_file.closed

    def _send_object(self, name: str, value):
        # select channel
        if self.is_server:
            f = self.motor_file
        else:
            f = self.sensor_file

        if f.closed:
            print('channel was closed, cannot write data')
            return

        # name
        x = str.encode(name)
        f.write(struct.pack('h', len(x)))
        f.write(x)

        # value
        x = pickle.dumps(value)
        f.write(struct.pack('l', len(x)))
        f.write(x)

        f.flush()

    def _read_object(self):
        # select channel
        if self.is_server:
            f = self.sensor_file
        else:
            f = self.motor_file

        if f.closed:
            print('channel was closed, cannot read data')
            return '', []

        # name
        n, = struct.unpack('h', f.read(2))
        name = f.read(n).decode()

        # value
        n, = struct.unpack('l', f.read(4))
        value = pickle.loads(f.read(n))

        return name, value

    def send_sensor(self, name, value):
        if self.is_server:
            raise Exception('Server cannot send sensor data')
        self._send_object(name, value)

    def send_motor(self, name, value):
        if not self.is_server:
            raise Exception('Client cannot send motor data')
        self._send_object(name, value)

    def read_sensor(self):
        if not self.is_server:
            raise Exception('Client cannot read sensor data')
        return self._read_object()

    def read_motor(self):
        if self.is_server:
            raise Exception('Server cannot read motor data')
        return self._read_object()


