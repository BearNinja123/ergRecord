import matplotlib.pyplot as plt
plt.switch_backend('agg')

import pandas as pd
import numpy as np
import os, datetime

# takes the .csv file for the workouts and cleans the data to produce a Dataframe (if specifying a specific HR zone) or a GroupBy object
def gen_hist_df(path='workouts', csv_name='workouts.csv', zone=None): # e.g. zone = 'UT2'
    try:
        df = pd.read_csv(os.path.join(path, csv_name))
    except FileNotFoundError:
        return False

    df = df.groupby('zone')

    if zone is None:
        return df
    else:
        return df.get_group(zone)

# takes a HR zone (e.g. UT2) and plots its historical data either of average workout splits or heart rate
def plot_zone_data(zone, mode='split', df=None, **kwargs):
    if df is None:
        df = gen_hist_df(zone)


    fig, ax = plt.subplots() 
    fig.suptitle('Historical {} Workout Data ({})'.format(zone, mode)) 

    dates = []
    for index, workout in df.iterrows(): # for each row in the workout category (each workout), get the workout's date of completion
        ymdhm = [] # store data for putting into a datetime object
        for period in ['year', 'month', 'day', 'hour', 'minute']:
            ymdhm.append(workout[period])
        dates.append(datetime.datetime(*ymdhm))

    ys = df['avg_{}'.format(mode.lower())]
    ax.set_ylim([min(ys) - 1, max(ys) + 1])
    ax.tick_params(labelsize=10)
    plt.plot_date(dates, ys, **kwargs) # plot them workout historical data
    plt.xticks(rotation=15)
    return fig

def empty_graph(title):
    fig, _ = plt.subplots() 
    fig.suptitle(title)
    return fig
