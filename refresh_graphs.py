# In case a workout had to be placed manually, run this program to update the historical data workout graphs.
import app.historical_data_plot as hdp

for zone in ['UT1', 'UT2', 'UT3', 'AT', 'TRANS', '2K']:
    try:
        df = hdp.gen_hist_df(zone=zone)
        split_fig = hdp.plot_zone_data(zone, mode='Split', df=df, color='green')
        split_fig.savefig('images/{}/{}_historical_split.jpg'.format(zone, zone))
        hr_fig = hdp.plot_zone_data(zone, mode='HR', df=df, color='red')
        hr_fig.savefig('images/{}/{}_historical_hr.jpg'.format(zone, zone))
    except:
        pass
