from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Flask, Response, render_template, jsonify, request, flash, send_file
from PIL import Image

import numpy as np
import app.historical_data_plot as hdp
import app.erg_monitor as erg_monitor
import app.formatting as formatting
import io, time, json, os

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

debug = False
app = Flask(__name__)
app.secret_key = b'j;oafijopiewjf oijfpOI JOI jpIOPJF'

rest_hr = max_hr = hrr = age = None
outdir = 'workouts'
try:
    if 'rest_hr.npy' in os.listdir(outdir):
        rest_hr = int(np.load(os.path.join(outdir, 'rest_hr.npy')))
        max_hr = int(np.load(os.path.join(outdir, 'max_hr.npy')))
        hrr = max_hr - rest_hr # hrr = heart rate reserve
except FileNotFoundError:
    pass

split = hr = None
lookback = 60
sum_points_every = 5
monitor = erg_monitor.ErgMonitor(debug=debug, lookback=lookback)
sendImage = clearFig = False
current_workout_zone = past_workout_zone = None
hsd = hhd = None # hsd/hhd = historical split/HR data
reload_time = 1 # amount of time in seconds to update live data

def load_empty_graphs(): # if there's no image for a workout category, make an empty graph for it
    df = hdp.gen_hist_df() # create data with all historical data

    for zone in ['2K', 'TRANS', 'AT', 'UT1', 'UT2', 'UT3']: # for each zone, try to get split and HR data, if you can't, get empty graphs and save them
        file_dir = 'images/' + zone
        try:
            os.listdir(file_dir)
        except FileNotFoundError:
            os.mkdir(file_dir)

        if '{}_historical_split.jpg'.format(zone) not in os.listdir(file_dir):
            split_fig = hdp.empty_graph('Historical {} Workout Data (Split)'.format(zone))
            split_fig.savefig('{}/{}_historical_split.jpg'.format(file_dir, zone))
            hr_fig = hdp.empty_graph('Historical {} Workout Data (HR)'.format(zone))
            hr_fig.savefig('{}/{}_historical_hr.jpg'.format(file_dir, zone))

# get a figure from the monitor and return it as a generator to display on the website
def gen_figure():
    global sendImage, clearFig

    while True:
        fig = monitor.cug() # get the fig
        output = io.BytesIO() # create a place to dump the contents of the figure into
        FigureCanvas(fig).print_jpeg(output) # turn the figure into a png file but just in memory
        ret = output.getvalue()

        # sendImage is true when jQuery requests data so the image and the split/HR data is sent (and thus displayed) on the web page at the same time
        while not sendImage:
            time.sleep(0.01)
            if clearFig: # if the "clear workout" button is pressed, clearFig is True
                monitor.clear_data()
                fig = monitor.cug() # plot an empty graph
                output = io.BytesIO() # create a place to dump the contents of the figure into
                FigureCanvas(fig).print_jpeg(output) # turn the figure into a png file but just in memory
                ret = output.getvalue()
                clearFig = False

        sendImage = False
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + ret + b'\r\n\r\n') # you absolutely need all of this to work

# takes an image from disk (mainly from the 'images' folder) and displays it on a separate page on the website
@app.route('/images/<name>')
@app.route('/images/<folder>/<name>') # hacky way of doing things but i can't think of a better way
def get_img(name, path='images', folder=None):
    file_extension = name[name.index('.') + 1:]

    if folder is None:
        img = open(os.path.join(path, name), 'rb').read()
    else:
        img = open(os.path.join(path, folder, name), 'rb').read()

    return send_file(
        io.BytesIO(img),
        mimetype='image/{}'.format(file_extension),
        as_attachment=True, download_name=name)

# calculates data to be sent to the website
@app.route('/_data')
def send_data(lookback=lookback):
    global sendImage, hsd, hhd, past_workout_zone
    sendImage = True

    # data that will be sent
    fields = {
        'split': 'N/A',
        'avg_split': 'N/A',
        'past_split': 'N/A',
        'hr': 'N/A',
        'avg_hr': 'N/A',
        'past_hr': 'N/A',
        'current_hr_zone': 'N/A',
        'hr_color': 'N/A', # high hr - red, low hr - green
    }

    if monitor.hr is None: # if monitor.hr hasn't even be set, there's going to be no other data fields set
        return jsonify(fields)

    if rest_hr is None or not type(rest_hr) is int:
        fields['current_hr_zone'] = 'Error: Please fill out the form in the "Form" tab to see what zone you are currently in.'
    else:
        percent_heart_rate = (monitor.hr - rest_hr) / hrr
        fields['current_hr_zone'] = formatting.calc_hr_zone(percent_heart_rate)
        fields['hr_color'] = formatting.hr_zone_coloring(percent_heart_rate)

    fields['split'] = formatting.fmt_split(monitor.split)
    fields['hr'] = round(monitor.hr)

    if monitor.split == 0: # at least for when the erg is sending data, monitor.split is 0 when the erg is paused (no rowing happening)
        fields['split'] = 'N/A'
    if monitor.hr == 0:
        fields['hr'] = 'N/A'

    avg_split, avg_hr = monitor.get_averages(lookback)
    if not np.isnan(avg_split): # avg_split (and avg_hr) will be nan if numpy was trying to take the mean of an empty list
        fields['avg_split'] = formatting.fmt_split(avg_split)
        fields['avg_hr'] = round(avg_hr)
    else:
        fields['avg_split'] = fields['avg_hr'] = 'N/A'

    observed_workout_timestep = monitor.timestep // sum_points_every + 1

    # try to find a comparable split from a past workout
    if rest_hr is not None: # if no resting and max HR --> no workout zones --> can't get a split from a past workout in that zone
        hhd_too_small = hhd is not None and observed_workout_timestep > hhd.shape[0]
        workout_changed = past_workout_zone != current_workout_zone
        if (hhd_too_small or workout_changed) and current_workout_zone is not None:
            hsd, hhd = monitor.find_nearest_historical(current_workout_zone)
            past_workout_zone = current_workout_zone # if workout changed, acknowledge the new workout into the past workout, if it didn't change, this line doesn't do anything

        if hsd is not None:
            fields['past_split'] = formatting.fmt_split(hsd[observed_workout_timestep - 1]) # observed_workout_timestep is 1-indexed so adjust to make it 0-indexed
            fields['past_hr'] = round(hhd[observed_workout_timestep - 1])
        
    return jsonify(fields)

# get the data from the form when submitted and save it
@app.route('/form', methods=['GET', 'POST'])
def submit_form():
    global hrr, rest_hr, max_hr, age

    # collect data found in the post request and calculating rest/max HR
    if request.method == 'POST': 
        form_data = request.form
        rest_hr, age, max_hr = form_data['rest_hr'], form_data['age'], form_data['max_hr']

        # qualifying and processing string data 
        if not rest_hr.isdigit():
            flash('Please provide your resting heart rate (default is 60 BPM) as an integer.')
            return render_template('form.html', rest_hr=60, age=age, max_hr=max_hr)
        elif (not age.isdigit()) and (not max_hr.isdigit()):
            flash('Please provide either your max heart rate or your age as an integer.')
            return render_template('form.html', rest_hr=rest_hr, age='', max_hr='')
        else: # turn data received into ints and saving them to disk
            rest_hr = int(rest_hr)
            if not max_hr.isdigit():
                max_hr = 220 - int(age)
            max_hr = int(max_hr)
            hrr = max_hr - rest_hr

            try:
                os.mkdir(outdir)
            except FileExistsError:
                pass
            np.save(os.path.join(outdir, 'rest_hr.npy'), rest_hr)
            np.save(os.path.join(outdir, 'max_hr.npy'), max_hr)

    if rest_hr is None: # put this condition below data collection so you can change rest_hr if there is a post request
        return render_template('form.html', rest_hr=60, age='', max_hr='')

    # taking rest/max HR (whether it be from the post request or saved in disk) and calculating HR zones
    zone_bpm = lambda zone: round(rest_hr + hrr * zone / 100)

    trans = '{}-{}'.format(zone_bpm(90), zone_bpm(100))
    at = '{}-{}'.format(zone_bpm(80), zone_bpm(90))
    ut1 = '{}-{}'.format(zone_bpm(70), zone_bpm(80))
    ut2 = '{}-{}'.format(zone_bpm(60), zone_bpm(70))
    ut3 = '{}-{}'.format(zone_bpm(50), zone_bpm(60))

    # render 'em templates
    if age is None:
        age = ''

    return render_template(
        'form.html', rest_hr=rest_hr, age=age,
        max_hr='', hrr=hrr,
        calc_max_hr=max_hr, trans_zone=trans, at_zone=at,
        ut1_zone=ut1, ut2_zone=ut2, ut3_zone=ut3)

# get the zone that the user selected, then display pictures of the historical workout data of that zone
@app.route('/hist_data', methods=['GET', 'POST'])
def view_hdata():
    if request.method == 'POST':
        zone = request.form['workout_type']
        return render_template('historical_data.html',
            split_pic='/images/{}/{}_historical_split.jpg'.format(zone, zone),
            hr_pic='/images/{}/{}_historical_hr.jpg'.format(zone, zone))
    return render_template('historical_data.html')

# take a figure and send it to the web page
@app.route('/plot')
def plot():
    return Response(gen_figure(), mimetype='multipart/x-mixed-replace; boundary=frame') # you absolutely need all of this to work

# process button/workout selection input in the live data (the default) page and display the page
@app.route('/', methods=['GET', 'POST'])
def index():
    global clearFig, current_workout_zone, past_workout_zone

    if request.method == 'POST':
        if 'button_clicked' in request.form:
            if request.form['button_clicked'] == 'save':
                if current_workout_zone != '2K':
                    avg_every = sum_points_every
                else:
                    avg_every = 1 # for 2ks, record and store all data

                monitor.dump_data(zone=current_workout_zone, rest_hr=rest_hr, max_hr=max_hr, avg_every=avg_every, outdir='workouts')

                df = hdp.gen_hist_df(zone=current_workout_zone)
                split_fig = hdp.plot_zone_data(current_workout_zone, mode='Split', df=df, color='green')
                split_fig.savefig('images/{}/{}_historical_split.jpg'.format(current_workout_zone, current_workout_zone))
                hr_fig = hdp.plot_zone_data(current_workout_zone, mode='HR', df=df, color='red')
                hr_fig.savefig('images/{}/{}_historical_hr.jpg'.format(current_workout_zone, current_workout_zone))
            elif request.form['button_clicked'] == 'clear':
                clearFig = True
        elif 'workout_type' in request.form:
            past_workout_zone = current_workout_zone
            current_workout_zone = request.form['workout_type']

    return render_template('index.html', reload_time=reload_time)

# if needed, make empty graphs so the section of historical data for each zone shows a figure
load_empty_graphs()

if __name__ == '__main__':
    if debug:
        app.run(debug=True)
        #app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0')
