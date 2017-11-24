import matplotlib.pyplot as plt
import numpy as np

import AlphaI


class Display:

    # noinspection PyPep8Naming
    def __init__(self, AI):  # AlphaI.AI):
        # Keep link on AI
        self.AI = AI

        # Turn Matplotlib interactive mode on
        plt.ion()

        # Init display
        self.fig = plt.figure()
        nt = AlphaI.history_length
        tt = np.reshape(list(range(nt)), (nt, 1))
        print(len(tt))

        self.ax, self.hl = [None]*4, [None]*4
        titles = ['Front Infra-Red', 'Line-tracking Infra-Red',
                  'Speed', 'Motor commands']
        # noinspection SpellCheckingInspection
        ylims = [(0, 1000), (0, 1000), (-100, 100), (-100, 100)]
        nlines = [2, 5, 2, 2]
        for i in range(4):
            self.ax[i] = self.fig.add_subplot(4, 1, 1+i)
            self.hl[i] = self.ax[i].plot(np.tile(tt, (1, nlines[i])),
                                         np.zeros((nt, nlines[i])))
            # self.ax[i].set_xlim(0, nt)
            # self.ax[i].set_autoscaley_on(True) #set_ylim(ylims[i])
            self.ax[i].set_title(titles[i])

    def update(self):
        data = self.AI.sensor
        hist = self.AI.sensor_history

        # Front IR
        self.hl[0][0].set_ydata(hist.IR_left)
        self.hl[0][1].set_ydata(hist.IR_right)

        # Line IR
        x = hist.IR_line
        x = x - x.mean(axis=0)
        for i in range(5):
            self.hl[1][i].set_ydata(x[..., i])

        # Speed
        for i in range(2):
            self.hl[2][i].set_ydata(hist.speed[..., i])

        # Motor
        for i in range(2):
            self.hl[3][i].set_ydata(self.AI.motor_history[..., i])

        # Axes limits
        for i in range(4):
            self.ax[i].relim()
            self.ax[i].autoscale_view(tight=False)

        # Redraw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
