from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Flask, Response, render_template, jsonify, request, flash
import ergMonitorHR, stringFmt
import io, time, json

debug = True
app = Flask(__name__)
app.secret_key = b'j;oafijopiewjf oijfpOI JOI jpIOPJF'
split = hr = None
hrr = None # heart rate reserve

def genFigure(reloadTime=1): # reloadTime = number of seconds to wait before yielding a value
    global split, hr

    while True:
        start = time.time()

        if split is None:
            wait = False
        else:
            wait = True

        fig, split, hr = ergMonitorHR.updateData(debug=debug)
        output = io.BytesIO() # create a place to dump the contents of the figure into
        FigureCanvas(fig).print_jpeg(output) # turn the figure into a png file but just in memory
        ret = output.getvalue()

        duration = time.time() - start

        if wait:
            time.sleep(max(0, reloadTime - duration)) # ensure that each yield takes the proper amount of time:

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + ret + b'\r\n\r\n') # you absolutely need all of this to work

@app.route('/_splits')
def seeData(lookback=60): # calculate split and HR averages every 60 timesteps
    fields = {
            'split': 'N/A',
            'avgSplit': 'N/A',
            'hr': 'N/A',
            'avgHr': 'N/A',
        }

    if hr is not None:
        fields['split'] = stringFmt.fmtSplit(split)
        fields['hr'] = str(round(hr))

        avgSplit, avgHr = ergMonitorHR.getAverages(lookback)
        fields['avgSplit'] = stringFmt.fmtSplit(avgSplit)
        fields['avgHr'] = str(round(avgHr))
        
    return jsonify(fields)

@app.route('/form', methods=['GET', 'POST'])
def submitForm():
    global hrr

    if request.method == 'POST':
        formData = request.form
        restHR, age, maxHR = formData['restHR'], formData['age'], formData['maxHR']

        if not restHR.isdigit():
            flash('Please provide your resting heart rate (default is 60 BPM) as an integer.')
        elif (not age.isdigit()) and (not maxHR.isdigit()):
            flash('Please provide either your max heart rate or your age as an integer.')
        else:
            if not maxHR.isdigit():
                maxHR = 220 - int(age)
            hrr = int(maxHR) - int(restHR)
            return render_template('form.html', maxHR=maxHR, hrr=hrr)

        print(request.form)
        print(request.form['restHR'])
    return render_template('form.html')

@app.route('/hist_data')
def viewHData():
    return render_template('historical_data.html')

@app.route('/plot')
def plot():
    return Response(genFigure(), mimetype='multipart/x-mixed-replace; boundary=frame') # you absolutely need all of this to work

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if debug:
        app.run(debug=True)
        #app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0')
