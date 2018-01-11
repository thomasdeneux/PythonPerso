import numpy as np
import random
import time
import math

from Utils import *
import Communication
import GUI

from gym import Env, spaces
from gym.utils import seeding
from baselines import deepq


class AlphaHub:

    def __init__(self, channel: Communication.ClientServerChannel, do_gui=True, history_length=100, max_speed=50):
        # Channel
        self.channel = channel

        # Current values and history
        self.sensor = None          # type: Communication.SensorData
        self.motor = np.zeros(2)    # current motor

        # History
        self.history_length = history_length
        self.sensor_history = Communication.SensorData()    # sensor history
        self.sensor_history.IR_left = np.zeros(self.history_length)
        self.sensor_history.IR_right = np.zeros(self.history_length)
        self.sensor_history.IR_line = np.zeros((self.history_length, 5))
        self.sensor_history.speed = np.zeros((self.history_length, 2))
        self.motor_history = np.zeros((self.history_length, 2))  # motor history

        # Display
        self.do_gui = do_gui
        if self.do_gui:
            self.gui = GUI.Display(self)

        # Other options
        self.max_speed = max_speed

        # Steps will always consist of (send command) then (read sensor), but the robot itself already sent a first
        # sensor data, so we need to pop it out before sending the first command
        self._read_sensor()

    def reset(self):
        # Stop robot
        self.step([0, 0])

        # Reset history
        self.sensor_history = Communication.SensorData()    # sensor history
        self.sensor_history.IR_left = np.zeros(self.history_length)
        self.sensor_history.IR_right = np.zeros(self.history_length)
        self.sensor_history.IR_line = np.zeros((self.history_length, 5))
        self.sensor_history.speed = np.zeros((self.history_length, 2))
        self.motor_history = np.zeros((self.history_length, 2))  # motor history

        # Update display
        if self.do_gui:
            self.render()

    def cleanup(self):
        # Stop robot
        try:
            self.step([0, 0])
        except:
            pass
        # Close channel
        self.channel.cleanup()

    def _read_sensor(self):
        # Read sensor data from channel
        name, data = self.channel.read_sensor()
        if name != 'IR':
            raise Exception('no sensor data')
        self.sensor = data

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

    def _send_motor(self, motor):
        # Send motor command to channel
        self.motor[0] = max(-self.max_speed, min(self.max_speed, motor[0]))
        self.motor[1] = max(-self.max_speed, min(self.max_speed, motor[1]))
        self.channel.send_motor('motor', self.motor)

        # Update history
        self.motor_history[:-1, ...] = self.motor_history[1:, ...]
        self.motor_history[-1, ...] = self.motor

    def render(self):
        if self.do_gui:
            self.gui.update()

    def step(self, motor):
        # Send motor
        self._send_motor(motor)
        # Read sensor
        self._read_sensor()
        # Update display
        self.render()

    # Main loop
    def go_random(self):
        try:
            # Note that it is the client side that sets the loop frequency
            while not self.channel.is_closed():
                # Motor command: Brownian motion!
                decay = 0
                noise = 5
                new_motor = [self.motor[0] * (1. - decay) + random.uniform(-1., 1.) * noise,
                            self.motor[1] * (1. - decay) + random.uniform(-1., 1.) * noise]
                self.step(new_motor)
        finally:
            self.cleanup()


class AlphaEnv(Env):

    def __init__(self, channel, max_speed=50, nstack=3, nstep=1, motion_threshold=5, do_gui=True, episode_length=20,
                 action_space='discrete'):
        # Connect to AlphaBot
        self.hub = AlphaHub(channel, max_speed=max_speed, do_gui=False)

        # Input
        self.observation_names = [  #'IRleft', 'IRleft_up', 'IRleft_down', 'IRright', 'IRright_up', 'IRright_down',
                                  'SD', #''SDleft_abs', 'SDright_abs', #'SDleft_pos', 'SDleft_neg', 'SDright_pos', 'SDright_neg',
                                  'Mforward', 'Mturnleft', 'Mturnright']  #, 'Mbackward']
        self.nobs = len(self.observation_names)
        self.observation_signed = [False] * self.nobs
        self.nstack = nstack
        self.observation_space = spaces.Box(np.repeat(-np.array(self.observation_signed, dtype='float'), nstack),
                                            np.ones(self.nobs*self.nstack))
        self.observation_range =  np.ones((2, self.nobs)) * [[1000], [-1000]] # this range will be used to
        # rescale observations between 0 and 1, and will be continuously adjusted
        self.observation_stack = np.zeros((self.nobs, self.nstack))

        # Output
        self.action_names = ['forward',  #'backward',
                             'left_backward', #'left_forward', 'left',
                             'right_backward'] #, 'right_forward', 'right', ]
        self.naction = len(self.action_names)
        self.action_space = spaces.Discrete(self.naction)

        # Reward
        self.max_motion = 60 # Will be used to rescale reward between 0 and 1
        self.motion_threshold = motion_threshold  # This threshold for detecting if there is motion is manually adjusted
        self.reward_range = (-1, 1)

        # Number of data collections per new motor command
        self.nstep = nstep

        # Count time steps for fixed episode length
        self.step_count = 0
        self.episode_length = episode_length

        # Init display
        if do_gui:
            self.history_length = self.hub.history_length
            self.observation_history = np.zeros((self.history_length, self.nobs))
            self.reward_history = np.zeros(self.history_length)
            self.GUI = GUI.Display(self.hub, self)
        else:
            self.GUI = None

    def _step(self, action):
        # Translate action into motor command
        if isinstance(action, (int, np.int64)):
            action_name = self.action_names[action]
        else:
            action_name = action
        max_speed = self.hub.max_speed

        if action_name=='stop':
            motor = [0, 0]
        elif action_name=='forward':
            motor = [max_speed, max_speed]
        elif action_name=='backward':
            motor = [-max_speed, -max_speed]
        elif action_name == 'left_forward':
            motor = [0, max_speed]
        elif action_name == 'left':
            motor = [-max_speed, max_speed]
        elif action_name == 'left_backward':
            motor = [-max_speed, 0]
        elif action_name=='right_forward':
            motor = [max_speed, 0]
        elif action_name=='right':
            motor = [max_speed, -max_speed]
        elif action_name=='right_backward':
            motor = [0, -max_speed]
        else:
            raise Exception('unknown action:', action_name)

        # Send command and get sensor data (repeat nstep times)
        for i in range(self.nstep):
            self.hub.step(motor)

        # Translate sensor data into input
        # (some precomputations)
        hist = self.hub.sensor_history
        motor = self.hub.motor
        x = np.arange(self.nstep + 1)
        x = x - x.mean()
        y = hist.IR_left[-self.nstep - 1:]
        y = y - y.mean()
        IRleft_slope = (x * y).sum() / (x ** 2).sum()
        y = hist.IR_right[-self.nstep - 1:]
        y = y - y.mean()
        IRright_slope = (x * y).sum() / (x ** 2).sum()
        speed_left = math.copysign(hist.speed[-self.nstep:, 0].mean(), motor[0])
        speed_right = math.copysign(hist.speed[-self.nstep:, 1].mean(), motor[1])
        # (assign observations)
        obs = np.zeros(self.nobs)
        for i, name in enumerate(self.observation_names):
            if name == 'IRleft':
                obs[i] = hist.IR_left[-self.nstep:].mean()
            elif name == 'IRleft_slope':
                obs[i] = IRleft_slope
            elif name == 'IRleft_up':
                obs[i] = max(0, IRleft_slope)
            elif name == 'IRleft_down':
                obs[i] = max(0, -IRleft_slope)
            elif name == 'IRright':
                obs[i] = hist.IR_right[-self.nstep:].mean()
            elif name == 'IRright_slope':
                obs[i] = IRright_slope
            elif name == 'IRright_up':
                obs[i] = max(0, IRright_slope)
            elif name == 'IRright_down':
                obs[i] = max(0, -IRright_slope)
            elif name == 'SDleft':
                obs[i] = speed_left
            elif name == 'SDleft_abs':
                obs[i] = abs(speed_left)
            elif name == 'SDleft_pos':
                obs[i] = max(0, speed_left)
            elif name == 'SDleft_neg':
                obs[i] = max(0, -speed_left)
            elif name == 'SDright':
                obs[i] = speed_right
            elif name == 'SDright_abs':
                obs[i] = abs(speed_right)
            elif name == 'SDright_pos':
                obs[i] = max(0, speed_right)
            elif name == 'SD':
                obs[i] = abs(speed_left) + abs(speed_right)
            elif name == 'SDright_neg':
                obs[i] = max(0, -speed_right)
            elif name == 'Mforward':
                obs[i] = max(0, motor[0]+motor[1])/2
            elif name == 'Mbackward':
                obs[i] = max(0, -motor[0]-motor[1])/2
            elif name == 'Mturnleft':
                obs[i] = max(0, motor[1]-motor[0])/2
            elif name == 'Mturnright':
                obs[i] = max(0, motor[0]-motor[1])/2
            else:
                raise Exception('unknown observation name:' + name)

        # Rescale between 0 and 1, or between -1 and 1
        for i, is_signed in enumerate(self.observation_signed):
            if is_signed:
                self.observation_range[1, i] = np.maximum(self.observation_range[1, i], abs(obs[i]))
                obs[i] = obs[i] / self.observation_range[1, i]
            else:
                self.observation_range[0, i] = np.minimum(self.observation_range[0, i], obs[i])
                self.observation_range[1, i] = np.maximum(self.observation_range[1, i], obs[i])
                obs[i] = (obs[i] - self.observation_range[0, i]) / \
                         (self.observation_range[1, i] - self.observation_range[0, i])

        # Stack last observations
        self.observation_stack[..., :-1] = self.observation_stack[..., 1:]
        self.observation_stack[..., -1] = obs

        # Compute reward: robot must be actually moving, and cannot cheat with both wheels going in opposite directions
        nback = max(self.nstep+1, 5)  # compute std from at least 5 points
        IR_line_std = hist.IR_line[-nback:].std()
        motion = abs(speed_left) + abs(speed_right)
        #self.max_motion = max(self.max_motion, motion)
        if motion==0:
            reward = -1
        else:
            reward = motion / self.max_motion
            reward = max(0, (reward-.5)*2)  # actually give a reward only if speed is more than half the max!
            reward = min(1, reward)

        # Count time steps for fixed episode length
        self.step_count = (self.step_count + 1) % self.episode_length
        done = (self.step_count == 0)

        # Update display
        if self.GUI:
            self.observation_history[:-1, ...] = self.observation_history[1:, ...]
            self.observation_history[-1, ...] = obs
            self.reward_history[:-1] = self.reward_history[1:]
            self.reward_history[-1] = reward
            self.GUI.update()

        return self.observation_stack.ravel(), reward, done, {}

    def _reset(self):
        # No reset action as the robot never really stops, just return current observation
        return self.observation_stack.ravel()

    def _render(self, mode='human', close=False):
        # Note that there are some displays occurring during the step already
        pass

    def _close(self):
        self.hub.cleanup()

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]


def AI_deepq(channel: Communication.ClientServerChannel):
    # hub = AlphaHub(channel)
    # # hub.go_random()
    # hub.step([30, 30])
    # time.sleep(1)
    # hub.step([-30, -30])
    # time.sleep(1)
    # hub.step([30, -30])  # turn right
    # time.sleep(1)
    # hub.step([-30, 30])  # turn left
    # time.sleep(1)
    # hub.cleanup()


    env = AlphaEnv(channel, motion_threshold=5, do_gui=True, max_speed=40)
    # while True:
    #     action = env.action_space.sample()
    #     env.step(action)
    model = deepq.models.mlp([40, 20])
    act = deepq.learn(
        env,
        q_func=model,
        lr=1e-3,  # 1e-3
        max_timesteps=100000,
        buffer_size=50000,  # 50000
        exploration_fraction=0.001,  # 0.02
        exploration_final_eps=0.02,
        print_freq=1,
        callback=None
    )
    print("Saving model to AlphaI.pkl")
    act.save("AlphaI.pkl")


def AI_classic(channel: Communication.ClientServerChannel):

    # env = AlphaEnv(channel, motion_threshold=5, do_gui=True, max_speed=30)
    #
    # action = 'forward'
    # while True:
    #     obs, _, _, _ = env._step(action)
    #     obs = obs.reshape((env.nobs, env.nstack))
    #     s = dict()
    #     for i, name in enumerate(env.observation_names):
    #         s[name] = obs[i, :]
    #         if np.all(s['SD'] == 0):
    #             if random.random() < .5:
    #                 action = 'left_backward'
    #             else:
    #                 action = 'right_backward'
    #         else:
    #             action = 'forward'

    max_speed = 40
    hub = AlphaHub(channel, do_gui=False, max_speed=max_speed)

    while True:
        sensor = hub.sensor

        # If robot is blocked, randomly try one of the following actions to unblock him
        if np.array(sensor.speed).sum() == 0:

            r = random.randint(0, 3)
            if r == 0:
                motor = [-max_speed, 0]
            elif r == 1:
                motor = [0, -max_speed]
            elif r == 2:
                motor = [-max_speed, -max_speed*0.5]
            elif r == 3:
                motor = [-max_speed*0.5, -max_speed]
            else:
                raise Exception('random integer out of range')
            hub.step(motor)
            time.sleep(1)  # make a longer motion than usual

        # Go forward!
        hub.step([max_speed, max_speed])
        time.sleep(.5)


# Which function will actually be used for the robot intelligence
AI = AI_deepq










