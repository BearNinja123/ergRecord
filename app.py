from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Flask, Response, render_template, jsonify, request, flash
import erg_monitor, string_fmt
import io, time, json

debug = True
app = Flask(__name__)
app.secret_key = b'j;oafijopiewjf oijfpOI JOI jpIOPJF'
split = hr = None
rest_hr = max_hr = hrr = None # hrr = heart rate reserve
lookback = 60
monitor = erg_monitor.ErgMonitor(debug=debug, lookback=lookback)
sendImage = False
reload_time = 1

def test_func():
    pass

def gen_figure(lookback=lookback): # reload_time = number of seconds to wait before yielding a value
    global split, hr, sendImage

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
        hr_zones = {0.9: 'TRANS', 0.8: 'AT', 0.7: 'UT1', 0.6: 'UT2', 0.5: 'UT3'}

        if rest_hr is None or not type(rest_hr) is int:
            fields['current_hr_zone'] = 'Error: Please fill out the form in the "Form" tab to see what zone you are currently in.'
        else:
            percent_heart_rate = (hr - rest_hr) / hrr
            heart_rate_zone = int(percent_heart_rate * 10) / 10 # fancy truncation math to see which zone you're in

            if percent_heart_rate >= 0.5:
                fields['current_hr_zone'] = hr_zones[heart_rate_zone]

                # calculating the color for heart rate - 0.75 is between 0.5 (start of UT3) and 1.0 (max HR)
                if percent_heart_rate - 0.75 > 0:
                    redValue = 255
                    greenValue = int(255 + 255 * 4 * (0.75 - percent_heart_rate))
                else: 
                    greenValue = 255
                    redValue = int(255 - 255 * 4 * (0.75 - percent_heart_rate))
                fields['hr_color'] = 'rgb({}, {}, 0)'.format(redValue, greenValue)
            else:
                fields['current_hr_zone'] = 'SUB UT3'
                fields['hr_color'] = 'rgb(0, 255, 0)' # green

        fields['split'] = string_fmt.fmt_split(split)
        fields['hr'] = str(round(hr))

        if split == 0:
            fields['split'] = 'N/A'
        if hr == 0:
            fields['hr'] = 'N/A'

        avg_split, avg_hr = monitor.get_averages(lookback)
        fields['avg_split'] = string_fmt.fmt_split(avg_split)
        fields['avg_hr'] = str(round(avg_hr))
        
    return jsonify(fields)

@app.route('/form', methods=['GET', 'POST'])
def submit_form():
    global hrr, rest_hr, max_hr

    if request.method == 'POST':
        #print(request.form)
        #print(request.form['rest_hr'])

        form_data = request.form
        rest_hr, age, max_hr = form_data['rest_hr'], form_data['age'], form_data['max_hr']

        if not rest_hr.isdigit():
            flash('Please provide your resting heart rate (default is 60 BPM) as an integer.')
        elif (not age.isdigit()) and (not max_hr.isdigit()):
            flash('Please provide either your max heart rate or your age as an integer.')
        else:
            rest_hr = int(rest_hr)
            if not max_hr.isdigit():
                max_hr = 220 - int(age)
            hrr = int(max_hr) - int(rest_hr)

            zone_bpm = lambda zone: round(rest_hr + hrr * zone / 100)

            trans = '{}-{}'.format(zone_bpm(90), zone_bpm(100))
            at = '{}-{}'.format(zone_bpm(80), zone_bpm(90))
            ut1 = '{}-{}'.format(zone_bpm(70), zone_bpm(80))
            ut2 = '{}-{}'.format(zone_bpm(60), zone_bpm(70))
            ut3 = '{}-{}'.format(zone_bpm(50), zone_bpm(60))

            return render_template(
                    'form.html', max_hr=max_hr, hrr=hrr,
                    trans_zone=trans, at_zone=at,
                    ut1_zone=ut1, ut2_zone=ut2, ut3_zone=ut3)
    return render_template('form.html')

@app.route('/hist_data', methods=['GET', 'POST'])
def view_hdata():
    if request.method == 'POST':
        print(request.form)
    return render_template('historical_data.html')

@app.route('/plot')
def plot():
    return Response(gen_figure(), mimetype='multipart/x-mixed-replace; boundary=frame') # you absolutely need all of this to work

@app.route('/')
def index():
    return render_template('index.html', reload_time=reload_time)

if __name__ == '__main__':
    if debug:
        app.run(debug=True)
        #app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0')
