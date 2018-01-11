import socket, struct, pickle
import time


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

    def __init__(self, side, robot_ip='10.0.0.1', interrupt_action=None):
        # are we on the server or client side?
        self.side = side
        if side == 'server':
            self.is_server = True
        elif side == 'client':
            self.is_server = False
        else:
            raise Exception("side argument must be either 'server' or "
                            "'client'")

        self.robot_ip = robot_ip
        self.sensor_socket = self.sensor_file = self.motor_socket = self.motor_file = None
        self.check_hand()
        
        # action to execute if channel has problem (can be set later by user)
        self.interrupt_action = interrupt_action
        
    def check_hand(self):
        # hand checking: it is actually the server that tries to connect the
        # client, because only the robot has a fix IP address...
        print('Hand checking (' + self.side + ' side)...')
        if self.is_server:
            # sensor stream
            ok = False
            while not ok:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((self.robot_ip, _SensorPort))
                    ok = True
                except:
                    s.close()
                    print(' [failed]')
                    time.sleep(1)
                    print('New attempt...')
            self.sensor_socket = s
            self.sensor_file = s.makefile('rb')
            # motor stream
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.robot_ip, _MotorPort))
            self.motor_socket = s  # timeout seems not necessary because read() returns an empty byte array when the
            # connection is lost
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
            self.motor_socket.settimeout(10)  # set a timeout because even when the WiFi is cut the socket does not
            # appear as closed on the robot side, so it can wait forever during read
            s0.close()
            self.motor_file = self.motor_socket.makefile('rb')
        print(' [done]')

    def cleanup(self):
        print('Cleaning up communication channel (' + self.side + ' side)')
        self.sensor_socket.close()
        self.sensor_file.close()
        self.motor_socket.close()
        self.motor_file.close()
        if self.interrupt_action:
            self.interrupt_action()

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
        f.write(struct.pack('<H', len(x)))
        f.write(x)

        # value
        x = pickle.dumps(value)
        f.write(struct.pack('<L', len(x)))
        f.write(x)

        f.flush()

    def _read_object(self):
        # select channel
        if self.is_server:
            f = self.sensor_file
        else:
            f = self.motor_file

        # Check that channel is alive
        try:
            two_bytes = f.read(2)
        except:
            broken = True
        else:
            broken = (len(two_bytes) == 0)
        if broken:
            print('Channel was closed, attempting to re-open it')
            self.cleanup()
            self.check_hand()
            # Communication is re-established, now both sides are waiting for reading, so let the robot (client) side
            #  read 'motor', [0 0] and send a new sensor data that the server side can read
            if self.is_server:
                # time.sleep(1)  # I had an error last time on the following line, maybe do we need to wait a bit?
                f = self.sensor_file
                two_bytes = f.read(2)
            else:
                return 'motor', [0, 0]
            
        # name
        n, = struct.unpack('<H', two_bytes)
        name = f.read(n).decode()

        # value
        n, = struct.unpack('<L', f.read(4))
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


