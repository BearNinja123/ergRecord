from app.views import app, debug

if __name__ == '__main__':
    if debug:
        app.run(debug=True)
        #app.run('0.0.0.0')
    else:
        app.run('0.0.0.0')
