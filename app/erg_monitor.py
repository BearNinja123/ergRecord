# pyrow library at https://github.com/droogmic/Py3Row
from pyrow.pyrow import PyErg
from pyrow import pyrow

import matplotlib.pyplot as plt
import numpy as np

import app.historical_data_plot as hdp
import app.formatting as formatting
import os

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
        self.clear_data()

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
        except NameError:
            pass

        return self.erg
    
    def _setup_fig(self):
        self.fig, self.ax = plt.subplots()
        self.fig.suptitle('Live Erg Data')

        self.hr_plot = None
        self.split_plot = None

    def clear_data(self):
        self.timestep = 0
        self.current_time = -1
        self.x = []
        self.hrs = []
        self.splits = []
        self.hr = self.split = None
        self.avg_hr = self.avg_split = None

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
            self.split_plot, = self.ax.plot(self.x, self.splits, color='green', label='Split')
            self.ax.set_ylim([min(min(self.hrs), min(self.splits)) - 10, max(max(self.hrs), max(self.splits)) + 10])
            self.ax.legend()
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

    def dump_data(self, avg_every=300, rest_hr=None, max_hr=None, outdir='.', csv_name='workouts.csv'): # take averages every 300 datapoints, zone is a value like 'UT2'
        num_sum_points = len(self.x) // avg_every
        n = num_sum_points * avg_every
        get_avgs = lambda arr: arr[:n].reshape(avg_every, num_sum_points).mean(axis=0) # reshape arr into 2D array, take mean of that array where each mean summarizes avg_every items
        hr_arr = np.array(self.hrs)
        split_arr = np.array(self.splits)
        
        avg_splits = get_avgs(split_arr)
        self.avg_split = round(split_arr.mean())
        #avg_split = formatting.fmt_split(split_arr.mean())

        avg_hrs = get_avgs(hr_arr)
        self.avg_hr = round(hr_arr.mean())

        # Save everything
        try:
            os.mkdir(outdir)
        except FileExistsError:
            pass
        os.chdir(outdir)
        
        try:
            if rest_hr is None:
                zone = 'unknown'
            else:
                hrr = max_hr - rest_hr
                percent_heart_rate = (self.avg_hr - rest_hr) / hrr
                zone = formatting.calc_hr_zone(percent_heart_rate)

                np.save('rest_hr.npy', rest_hr)
                np.save('max_hr.npy', max_hr)

            try:
                os.mkdir('hr_data')
                os.mkdir('split_data')
            except FileExistsError:
                pass

            mth, d, y, h, m = formatting.whats_the_time()
            time_extension = '{}-{}-{}_{}:{}'.format(y, m, d, h, m)
            split_filename = 'split_data/split_{}.npy'.format(time_extension)
            hr_filename = 'hr_data/hr_{}.npy'.format(time_extension)
            np.save(split_filename, avg_splits)
            np.save(hr_filename, avg_hrs)

            if csv_name not in os.listdir():
                outfile = open(csv_name, 'a')
                outfile.write('month,day,year,hour,minute,num_sum_points,zone,avg_split,avg_hr,split_file,hr_file\n')
            else:
                outfile = open(csv_name, 'a')

            outfile.write('{},{},{},{},{},{},{},{},{},{},{}\n'.format(
                mth, d, y, h, m, num_sum_points, zone, self.avg_split, self.avg_hr, split_filename, hr_filename))

            outfile.close()
            os.chdir('..')
        except Exception as e:
            print('Exception on method dump_data:', e)
            os.chdir('..')

    def find_nearest_historical(self, hr_zone=None, rest_hr=None, max_hr=None, path='workouts', csv_name='workouts.csv'):
        # generate the dataframe to scan which workout is long enough to compare to the current workout
        avg_hr = np.mean(self.hrs)

        if hr_zone is None:
            hr_zone = formatting.calc_hr_zone(hr=avg_hr, rest_hr=rest_hr, max_hr=max_hr)

        try:
            df = hdp.gen_hist_df(path=path, csv_name=csv_name, zone=hr_zone)
            if df is None:
                return None, None
        except KeyError: # df had no entries of the type of workout requested
            return None, None

        # load the most recent workout which is comparable to the current workout
        observed_workout_timestep = self.timestep // 300 + 1

        valid_workouts = df[df['num_sum_points'] >= observed_workout_timestep]

        if valid_workouts.shape[0] == 0: # no valid workouts
            return None, None

        workout = valid_workouts.iloc[-1]
        split_file, hr_file = workout['split_file'], workout['hr_file']
        split_data = np.load(os.path.join(path, split_file))
        hr_data = np.load(os.path.join(path, hr_file))

        return split_data, hr_data

if __name__ == '__main__':
    while True:
        monitor = ErgMonitor()
        monitor.update_data(show=True)
