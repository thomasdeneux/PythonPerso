import matplotlib
matplotlib.use('Qt5Agg')  # use Qt5 backend, interactive mode is faster than the default tk!
import matplotlib.pyplot as plt
import numpy as np
import time

import AlphaI


class Display:

    refresh_interval = 0.5  # refresh twice per second

    # noinspection PyPep8Naming
    def __init__(self, AU, AE=None):
        # Keep link on AI
        self.AU = AU
        self.AE = AE
        if AE:
            nrow = 4
            ncol = 2
        else:
            nrow = 3
            ncol = 1

        # Turn Matplotlib interactive mode on
        plt.ion()

        # Memorize time of last refresh
        self.last_refresh = 0

        # Init display
        self.fig = plt.figure()
        nt = AU.history_length
        tt = np.reshape(list(range(nt)), (nt, 1))

        self.ax, self.hl = [None]*3, [None]*3
        titles = ['Front Infra-Red', #'Line-tracking Infra-Red',
                  'Speed', 'Motor commands']
        nline = [2, 2, 2]
        if AE:
            pos = [5, 3, 1]
        else:
            pos = [1, 2, 3]
        for i in range(3):
            self.ax[i] = self.fig.add_subplot(nrow, ncol, pos[i])
            self.hl[i] = self.ax[i].plot(np.tile(tt, (1, nline[i])), np.zeros((nt, nline[i])))
            self.ax[i].set_title(titles[i])

        # Display of learning input/output as well?
        if not AE:
            return

        # Init second display
        self.ax2, self.hl2 = [None] * 4, [None] * 4
        # titles = ['Front Infra-Red', 'Speed', 'Motor', 'Reward']
        # nline = [6, 2, 4, 1]
        # pos = [6, 4, 2, 8]
        titles = ['Speed', 'Motor', 'Reward']
        nline = [1, 3, 1]
        pos = [4, 2, 8]
        for i in range(len(titles)):
            self.ax2[i] = self.fig.add_subplot(nrow, ncol, pos[i])
            self.hl2[i] = self.ax2[i].plot(np.tile(tt, (1, nline[i])), np.zeros((nt, nline[i])))
            if titles[i] == 'Reward':
                self.ax2[i].set_ylim((-1.1, 1.1))
            else:
                self.ax2[i].set_ylim((-0.1, 1.1))
            self.ax2[i].set_title(titles[i])

    def update(self):
        # Refresh only if more time has passed than refresh_interval
        if time.time() - self.last_refresh < self.refresh_interval:
            return
        self.last_refresh = time.time()

        data = self.AU.sensor
        hist = self.AU.sensor_history

        # Front IR
        self.hl[0][0].set_ydata(hist.IR_left)
        self.hl[0][1].set_ydata(hist.IR_right)

        # # Line IR
        # x = hist.IR_line
        # x = x - x.mean(axis=0)
        # for i in range(5):
        #     self.hl[1][i].set_ydata(x[..., i])

        # Speed
        for i in range(2):
            self.hl[1][i].set_ydata(hist.speed[..., i])

        # Motor
        for i in range(2):
            self.hl[2][i].set_ydata(self.AU.motor_history[..., i])

        # Axes limits
        for i in range(3):
            self.ax[i].relim()
            self.ax[i].autoscale_view(tight=False)

        # Env display
        if self.AE:
            x = self.AE.observation_history

            # # Front IR
            # for i in range(6):
            #     self.hl2[0][i].set_ydata(x[..., i])
            #
            # # Speed
            # for i in range(2):
            #     self.hl2[1][i].set_ydata(x[..., 6+i])
            #
            # # Motor
            # for i in range(4):
            #     self.hl2[2][i].set_ydata(x[..., 8+i])
            #
            # # Reward
            # self.hl2[3][0].set_ydata(self.AE.reward_history)

            # Speed
            self.hl2[0][0].set_ydata(x[..., 0])

            # Motor
            for i in range(3):
                self.hl2[1][i].set_ydata(x[..., 1+i])

            # Reward
            self.hl2[2][0].set_ydata(self.AE.reward_history)

        # Redraw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

