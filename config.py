from app.fields import Fields
from app import app

debug = True
lookback = 60
avg_every = 300
reload_time = 1

fields = Fields(debug=debug, lookback=lookback, avg_every=avg_every, reload_time=reload_time)
app.config['fields'] = fields
app.config['SECRET_KEY'] = 'a;dfjapioejf43;klgn4j;ljq;gjj:OIWJP$joij)(FJj0F'
