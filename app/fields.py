# There's a LOT of variables that gets accessed and modified through all of the pages of the site - this is what they are

from . import erg_monitor
import numpy as np
import os

class Fields:
    def __init__(self, debug=False, lookback=60, avg_every=300, reload_time=1):
        self.outdir = 'workouts'
        self.rest_hr = max_hr = hrr = age = None
        try:
            if 'rest_hr.npy' in os.listdir(self.outdir):
                self.rest_hr = int(np.load(os.path.join(self.outdir, 'rest_hr.npy')))
                self.max_hr = int(np.load(os.path.join(self.outdir, 'max_hr.npy')))
                self.hrr = self.max_hr - self.rest_hr # hrr = heart rate reserve
        except FileNotFoundError:
            pass

        self.debug = debug
        self.lookback = lookback
        self.avg_every = avg_every # when referring to summary workouts, this is how many datapoints are summized per summarized point 
        self.reload_time = reload_time # amount of time in seconds to update live data

        self.split = self.hr = None
        self.current_workout_zone = self.past_workout_zone = None
        self.send_image = self.clear_fig = False
        self.hsd = self.hhd = None # hsd/hhd = historical split/HR data
        self.monitor = erg_monitor.ErgMonitor(debug=self.debug, lookback=self.lookback, avg_every=self.avg_every)
