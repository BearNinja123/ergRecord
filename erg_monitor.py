# pyrow library at https://github.com/droogmic/Py3Row
from pyrow.pyrow import PyErg
from pyrow import pyrow

import matplotlib.pyplot as plt
import numpy as np

class ErgMonitor:
    '''
    Args:
    show - if True, display the figure in a separate GUI window, if False, don't
    debug - if True, make random data, if False, use data collected by erg
    lookback - number of datapoints that should be shown in the plot produced
    '''
    def __init__(self, show=False, debug=False, lookback=60):
        self.erg = self._find_erg()
        self._setup_fig()

        self.timestep = 0
        self.x = []
        self.hrs = []
        self.splits = []
        self.hr = self.split = None
        self.avg_hrs = self.avg_splits = [] # recording 5-minute averages of heart rate and split
        self.show = show
        self.debug = debug
        self.lookback = lookback

    def _find_erg(self): # return a PyErg object if found an erg, else return None
        self.erg = None

        for e in pyrow.find(): # find available ergs 
            self.erg = e # i'm only connected to one erg at a time so the first erg found will be the erg I want to examine

        try:
            self.erg = PyErg(erg) # turn the USB device into a PyErg object
            print('Erg found')
        except Exception as e:
            print(e)

        return self.erg
    
    def _setup_fig(self):
        self.fig = plt.figure()
        self.fig.suptitle('Live Erg Data')
        self.ax = self.fig.add_subplot()

        self.hr_plot = None
        self.split_plot = None
        self.current_time = -1

    # collect heart rate and split data from an erg or generate them
    def collect_data(self):
        if self.debug:
            self.hr = self.split = 150
            self.hr += np.random.normal() * 10
            self.split += np.random.normal() * 10
        else:
            stats = self.erg.get_monitor() # get stats like HR and split
            self.hr = stats['heartrate']
            self.split = stats['pace']
            self.past_time = self.current_time
            self.current_time = stats['time']

    # checks the data and processes them if it is meaningful
    def update_data(self):
        if self.debug or (self.current_time != self.past_time and self.split != 0): # if the data actually means something then log it down
            self.x.append(self.timestep)
            self.hrs.append(self.hr)
            self.splits.append(self.split)
            self.timestep += 1

    # plots the data and displays it if the user specified show=True when initializing an ErgMonitor object
    def graph_data(self):
        if len(self.x) <= self.lookback:
            self.ax.cla()
            for val in [0, 60, 120, 180, 240]:
                self.ax.axhline(val, color='gray', alpha=0.25)
            self.ax.set_yticks(np.arange(0, 250, 10))
            self.hr_plot, = self.ax.plot(self.x, self.hrs, color='red', label='Heart rate')
            self.split_plot, = self.ax.plot(self.x, self.splits, color='blue', label='Split')
            self.ax.set_ylim([min(min(self.hrs), min(self.splits)) - 10, max(max(self.hrs), max(self.splits)) + 10])
            plt.legend()
        else:
            visible_hrs = self.hrs[-self.lookback:]
            visible_splits = self.splits[-self.lookback:]
            self.hr_plot.set_ydata(visible_hrs) # update data, we don't care about updating xdata because that will make the lines go out of bounds from the figure
            self.split_plot.set_ydata(visible_splits)
            self.ax.set_ylim([min(min(visible_hrs), min(visible_splits)) - 10, max(max(visible_hrs), max(visible_splits)) + 10])
            self.fig.canvas.draw() # update figure
            self.fig.canvas.flush_events() # idk lol

        if self.show:
            plt.pause(0.01)

    def get_averages(self, lookback=60):
        lookback = min(lookback, len(self.x))
        return np.mean(self.splits[-lookback:]), np.mean(self.hrs[-lookback:])

    # collect, update, graph data
    def cug(self):
        self.collect_data()
        self.update_data()
        self.graph_data()
        return self.fig, self.split, self.hr

if __name__ == '__main__':
    while True:
        monitor = ErgMonitor()
        monitor.update_data(show=True)