# pyrow library at https://github.com/droogmic/Py3Row
from pyrow.pyrow import PyErg
from pyrow import pyrow

import matplotlib.pyplot as plt
import numpy as np

erg = None
for e in pyrow.find(): # find available ergs 
    erg = e # i'm only connected to one erg at a time so the first erg found will be the erg I want to examine

try:
    erg = PyErg(erg) # turn the USB device into a PyErg object
    print('Erg found')
except Exception as e:
    print(e)

# Graph HR wrt. time
timestep = 0
x = []
hrs = []
splits = []

fig = plt.figure()
fig.suptitle('Live Erg Data')
ax = fig.add_subplot()

hrPlot = None
splitPlot = None
currentTime = -1

'''
Get data from the erg and graph it into a plt figure.
Args:
show - if True, display the figure in a separate GUI window, if False, don't
debug - if True, make random data, if False, use data collected by erg
numTimestepsShown - number of datapoints that should be shown in the plot produced
'''
def updateData(show=False, debug=False, numTimestepsShown=120):
    global timestep, x, hrs, splits, fig, ax, hrPlot, splitPlot, currentTime

    if debug:
        hr = split = 120
        hr += np.random.normal() * 10
        split += np.random.normal() * 10
    else:
        stats = erg.get_monitor() # get stats like HR and split
        hr = stats['heartrate']
        split = stats['pace']
        pastTime = currentTime
        currentTime = stats['time']

    if debug or (currentTime != pastTime and split != 0): # if the data actually means something then log it down
        x.append(timestep)
        hrs.append(hr)
        splits.append(split)
        timestep += 1

    if len(x) <= numTimestepsShown:
        ax.cla()
        for val in [0, 60, 120, 180, 240]:
            ax.axhline(val, color='gray', alpha=0.25)
        ax.set_yticks(np.arange(0, 250, 10))
        hrPlot, = ax.plot(x, hrs, color='red', label='Heart rate')
        splitPlot, = ax.plot(x, splits, color='blue', label='Split')
        ax.set_ylim([min(min(hrs), min(splits)) - 10, max(max(hrs), max(splits)) + 10])
        plt.legend()
    else:
        visibleHRs = hrs[-numTimestepsShown:]
        visibleSplits = splits[-numTimestepsShown:]
        hrPlot.set_ydata(visibleHRs) # update data, we don't care about updating xdata because that will make the lines go out of bounds from the figure
        splitPlot.set_ydata(visibleSplits)
        ax.set_ylim([min(min(visibleHRs), min(visibleSplits)) - 10, max(max(visibleHRs), max(visibleSplits)) + 10])
        fig.canvas.draw() # update figure
        fig.canvas.flush_events() # idk lol

    if show:
        plt.pause(0.01)

    return fig, split, hr

def getAverages(lookback=60):
    lookback = min(lookback, len(x))
    return np.mean(splits[-lookback:]), np.mean(hrs[-lookback:])

if __name__ == '__main__':
    while True:
        updateData(show=True)
