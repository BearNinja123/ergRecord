def pre_pad(text, length=4, filler='0'): # turn '2' --> '02' as in '2:02'
    prepend = ''
    for _ in range(max(0, length - len(text))):
        prepend += filler
    return prepend + text

def fmt_split(split): # turn split=120 --> 2:00
    return '{}:{}'.format(int(split // 60), pre_pad(str(round(split % 60, 1))))
