from flask import Flask, render_template, request, session, redirect
import redis

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

app.secret_key = b'3298afkl;a3ha*"""fsaz'

@app.route('/')
def index():
    if 'serverName' in session and r.sismember('servers', session['serverName']):
        return redirect('/guess')
    return render_template('index.html')

@app.route('/join')
def join():
    if 'serverName' in session and r.sismember('servers', session['serverName']):
        return redirect('/guess')
    elif 'username' in request.args and 'serverName' in request.args:
        if r.sismember('servers', session['serverName']):
            username, servername = (request.args['username'], request.args['serverName'])
            session['username'] = username
            session['serverName'] = servername
            r.sadd("players:" + servername, username)
            return redirect('/guess')
        else:
            return index()
    else:
        return index()

@app.route('/host')
def host():
    if 'serverName' in session and r.sismember('servers', session['serverName']):
        return redirect('/guess')
    elif 'username' in request.args and 'serverName' in request.args:
        username, servername = request.args['username'], request.args['serverName']
        session['username'] = username
        session['serverName'] = servername

        r.sadd("servers", servername)
        r.sadd("servers:" + servername + ":players", username)
        r.set("servers:" + servername + ":host", username)

        return redirect('/guess')
    else:
        return index()

@app.route('/guess')
def guess():
    server_key = "servers:" + session['serverName']
    guess_key = server_key + ":guesses:" + session['username']
    made_guess = r.sismember(server_key + ":guesses", session['username'])
    
    if made_guess:
        return redirect('/results')
    elif 'lat' in request.args and 'lng' in request.args:
        guess = {'lat': request.args['lat'], 'lng': request.args['lng']}

        r.sadd(server_key + ":guesses", session['username'])
        r.hmset(guess_key, guess)

        if r.scard(server_key + ":guesses") == r.scard(server_key + ":players"):
            # TODO push to all clients
        return redirect('/results')
    else:
        return render_template('guess.html')

@app.route('/answer')
def answer():
    server_key = "servers:" + session['serverName']
    is_host  = r.get(server_key + ":host").decode('utf-8') == session['username']

    if not is_host:
        return redirect('/results')
    elif 'lat' in request.args and 'lng' in request.args:
        answer = {'lat': request.args['lat'], 'lng': request.args['lng']}

        r.hmset(server_key + ":answer", answer)
        return redirect('/results')
    else:
        return render_template('guess.html', answer=True)

@app.route('/results')
def results():
    server_key = "servers:" + session['serverName']
    is_host  = r.get(server_key + ":host").decode('utf-8') == session['username']

    if is_host and not r.exists(server_key + ":answer"):
        return redirect('/answer')

    return render_template('results.html')

