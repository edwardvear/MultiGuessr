from flask import Flask, render_template, request, session, redirect
import redis

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

app.secret_key = b'3298afkl;a3ha*"""fsaz'

@app.route('/')
def index():
    if 'serverName' in session and r.sismember('servers', session['serverName']):
        return redirect('/game')
    return render_template('index.html')

@app.route('/join')
def join():
    if 'serverName' in session and r.sismember('servers', session['serverName']):
        return redirect('/game')
    elif 'username' in request.args and 'serverName' in request.args:
        if r.sismember('servers', session['serverName']):
            username, servername = (request.args['username'], request.args['serverName'])
            session['username'] = username
            session['serverName'] = servername
            r.sadd("players:" + servername, username)
            return redirect('/game')
        else:
            return index()
    else:
        return index()

@app.route('/host')
def host():
    if 'serverName' in session and r.sismember('servers', session['serverName']):
        return redirect('/game')
    elif 'username' in request.args and 'serverName' in request.args:
        username, servername = request.args['username'], request.args['serverName']
        session['username'] = username
        session['serverName'] = servername
        r.sadd("servers", servername)
        r.sadd("servers:" + servername + ":players", username)
        r.set("servers:" + servername + ":host", username)
        return redirect('/game')
    else:
        return index()

@app.route('/game')
def game():
    if 'lat' in request.args and 'lng' in request.args:
        return "lat is {} and lng is {}".format(request.args['lat'], request.args['lng'])
    else:
        return render_template('game.html')

