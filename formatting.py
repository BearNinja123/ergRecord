# miscellaneous functions regarding formatting of all kinds

from datetime import datetime

def pre_pad(text, length=4, filler='0'): # turn '2' --> '02' as in '2:02'
    prepend = ''
    for _ in range(max(0, length - len(text))):
        prepend += filler
    return prepend + text

def fmt_split(split): # turn split=120 --> 2:00
    return '{}:{}'.format(int(split // 60), pre_pad(str(round(split % 60, 1))))

def hr_zone_coloring(percent_heart_rate):
    if percent_heart_rate >= 0.5:
        # calculating the color for heart rate - 0.75 is between 0.5 (start of UT3) and 1.0 (max HR)
        if percent_heart_rate - 0.75 > 0:
            redValue = 255
            greenValue = int(255 + 255 * 4 * (0.75 - percent_heart_rate))
        else: 
            greenValue = 255
            redValue = int(255 - 255 * 4 * (0.75 - percent_heart_rate))
        return 'rgb({}, {}, 0)'.format(redValue, greenValue)
    else:
        return 'rgb(0, 255, 0)' # green

def calc_hr_zone(percent_heart_rate):
    hr_zones = {0.9: 'TRANS', 0.8: 'AT', 0.7: 'UT1', 0.6: 'UT2', 0.5: 'UT3'}
    heart_rate_zone = int(percent_heart_rate * 10) / 10 # fancy truncation math to see which zone you're in

    if percent_heart_rate >= 0.5:
        return hr_zones[heart_rate_zone]
    else:
        return 'SUB UT3'

def whats_the_time():
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    hour = now.strftime('%H')
    minute = now.strftime('%M')

    return month, day, year, hour, minute
