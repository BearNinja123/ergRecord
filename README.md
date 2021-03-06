# ergRecord

A little Flask app to track some stats on your Concept 2 rower, especially heart rate if you have a heart rate sensor. You can see live split and heart rate data on a graph, enter in your resting and max heart rate and find your appropriate workout zones (which is saved to disk), and store historical data for erg workouts which can be graphed over time and guide you in how much to pace yourself for your next workout.

## Web App Screenshots
### Live Data
![Live data page](/figs/live_data_page.png)
### Heart Rate Form
![hr form page](/figs/hr_form_page.png)
### Historical Data Page
![hist data page](/figs/hist_data_page.png)

This project uses Py3Row, which is not on PyPI but can be found [here](https://github.com/droogmic/Py3Row).

I've only tested this on a Debian machine, and other Linux distros should be able to run this as long as you get Py3Row to work (I made an installation script for the module but will only work for machines with apt) but I don't think this can run on Windows or MacOS.

## How To Run
Install Py3Row and set up proper permissions to read from the erg monitor (script only tested on Debian with PM3 and PM5 monitors, will need sudo access)
```
./installPyrow.sh
```
NOTE: if you connected your erg to your computer before running the above script, you'll need to unplug then replug the USB to put the changes made by the script into effect.

Run the program
```
python3 run.py
```

By default, the app is on debug mode, meaning split and HR data will be generated. To get real data from an erg, go into config.py and change debug = True -> debug = False.

June 5 2022 note: If you find yourself manually editing the files in the workouts folder and you need to update the plots to reflect the edits you make, run:
```
python3 refresh_graphs.py
```
