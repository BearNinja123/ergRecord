from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Flask, Response, render_template, jsonify, request, flash
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import numpy as np
import historical_data_plot as hdp
import erg_monitor, formatting
import io, time, json, os

debug = True
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
monitor = erg_monitor.ErgMonitor(debug=debug, lookback=lookback)
sendImage = clearFig = False
reload_time = 1

def gen_figure(lookback=lookback): # reload_time = number of seconds to wait before yielding a value
    global split, hr, sendImage, clearFig

    while True:
        if split is None:
            wait = False
        else:
            wait = True

        fig, split, hr = monitor.cug()
        output = io.BytesIO() # create a place to dump the contents of the figure into
        FigureCanvas(fig).print_jpeg(output) # turn the figure into a png file but just in memory
        ret = output.getvalue()

        while not sendImage:
            time.sleep(0.01)
            if clearFig:
                fig, split, hr = monitor.cug()
                output = io.BytesIO() # create a place to dump the contents of the figure into
                FigureCanvas(fig).print_jpeg(output) # turn the figure into a png file but just in memory
                ret = output.getvalue()
                clearFig = False

        sendImage = False
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + ret + b'\r\n\r\n') # you absolutely need all of this to work

@app.route('/_data')
def send_data(lookback=lookback): # calculates data to be sent to the website
    global sendImage
    sendImage = True

    fields = {
            'split': 'N/A',
            'avg_split': 'N/A',
            'hr': 'N/A',
            'avg_hr': 'N/A',
            'current_hr_zone': 'N/A',
            'hr_color': 'N/A', # high hr - red, low hr - green
        }

    if hr is not None:
        if rest_hr is None or not type(rest_hr) is int:
            fields['current_hr_zone'] = 'Error: Please fill out the form in the "Form" tab to see what zone you are currently in.'
        else:
            percent_heart_rate = (hr - rest_hr) / hrr
            fields['current_hr_zone'] = formatting.calc_hr_zone(percent_heart_rate)
            fields['hr_color'] = formatting.hr_zone_coloring(percent_heart_rate)

        fields['split'] = formatting.fmt_split(split)
        fields['hr'] = str(round(hr))

        if split == 0:
            fields['split'] = 'N/A'
        if hr == 0:
            fields['hr'] = 'N/A'

        avg_split, avg_hr = monitor.get_averages(lookback)
        if not np.isnan(avg_split):
            fields['avg_split'] = formatting.fmt_split(avg_split)
            fields['avg_hr'] = str(round(avg_hr))
        else:
            fields['avg_split'] = fields['avg_hr'] = 'N/A'
        
    return jsonify(fields)

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

@app.route('/hist_data', methods=['GET', 'POST'])
def view_hdata():
    if request.method == 'POST':
        zone = request.form['workout_type']
        return render_template('historical_data.html',
                split_pic='static/{}_historical_split.jpg'.format(zone),
                hr_pic='static/{}_historical_hr.jpg'.format(zone))
    return render_template('historical_data.html')

@app.route('/plot')
def plot():
    return Response(gen_figure(), mimetype='multipart/x-mixed-replace; boundary=frame') # you absolutely need all of this to work

@app.route('/', methods=['GET', 'POST'])
def index():
    global clearFig

    if request.method == 'POST':
        if 'button_clicked' in request.form:
            if request.form['button_clicked'] == 'save':
                monitor.dump_data(rest_hr=rest_hr, max_hr=max_hr, outdir='workouts')

                zone = formatting.calc_hr_zone(hr=monitor.avg_hr, rest_hr=rest_hr, max_hr=max_hr)
                df = hdp.gen_hist_df(zone=zone)
                split_fig = hdp.plot_zone_data(zone, mode='Split', df=df, color='green')
                split_fig.savefig('static/{}_historical_split.jpg'.format(zone))
                hr_fig = hdp.plot_zone_data(zone, mode='HR', df=df, color='red')
                hr_fig.savefig('static/{}_historical_hr.jpg'.format(zone))
            elif request.form['button_clicked'] == 'clear':
                monitor.clear_data()
                clearFig = True

    return render_template('index.html', reload_time=reload_time)

if __name__ == '__main__':
    df = hdp.gen_hist_df() # create data with all historical data
    if df: # if there is historical data
        for zone in ['TRANS', 'AT', 'UT1', 'UT2', 'UT3']: # for each zone, try to get split and HR data, if you can't, get empty graphs and save them
            '''if '{}_historical_split.jpg'.format(zone) not in os.listdir('static'):
                split_fig = hdp.empty_graph('Historical {} Workout Data (Split)'.format(zone))
                split_fig.savefig('static/{}_historical_split.jpg'.format(zone))
                hr_fig = hdp.empty_graph('Historical {} Workout Data (Split)'.format(zone))
                hr_fig.savefig('static/{}_historical_hr.jpg'.format(zone))'''

            try:
                split_fig = hdp.plot_zone_data(zone, mode='Split', df=df.get_group(zone), color='green')
                split_fig.savefig('static/{}_historical_split.jpg'.format(zone))
                hr_fig = hdp.plot_zone_data(zone, mode='HR', df=df.get_group(zone), color='red')
                hr_fig.savefig('static/{}_historical_hr.jpg'.format(zone))
            except:
                split_fig = hdp.empty_graph('Historical {} Workout Data (Split)'.format(zone))
                split_fig.savefig('static/{}_historical_split.jpg'.format(zone))
                hr_fig = hdp.empty_graph('Historical {} Workout Data (Split)'.format(zone))
                hr_fig.savefig('static/{}_historical_hr.jpg'.format(zone))

    if debug:
        app.run(debug=True)
        #app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0')
