from flask import Flask, render_template, request, session, redirect, jsonify, abort
import redis

import math

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

app.secret_key = b'3298afkl;a3ha*"""fsaz'

@app.route('/')
def index():
    if 'roomName' in session and r.sismember('rooms', session['roomName']):
        return redirect('/guess')
    return render_template('index.html')

@app.route('/join')
def join():
    if 'roomName' in session and r.sismember('rooms', session['roomName']):
        return redirect('/guess')
    elif 'username' in request.args and 'roomName' in request.args:
        if r.sismember('rooms', request.args['roomName']):
            username, roomname = (request.args['username'], request.args['roomName'])
            session['username'] = username
            session['roomName'] = roomname
            r.sadd("rooms:" + roomname + ":players", username)
            return redirect('/guess')
        else:
            return index()
    else:
        return index()

@app.route('/host')
def host():
    if 'roomName' in session and r.sismember('rooms', session['roomName']):
        return redirect('/guess')
    elif 'username' in request.args and 'roomName' in request.args:
        username, roomname = request.args['username'], request.args['roomName']
        session['username'] = username
        session['roomName'] = roomname

        r.sadd("rooms", roomname)
        r.sadd("rooms:" + roomname + ":players", username)
        r.set("rooms:" + roomname + ":host", username)

        return redirect('/guess')
    else:
        return index()

@app.route('/guess')
def guess():
    room_key = "rooms:" + session['roomName']
    guess_key = room_key + ":guesses:" + session['username']
    made_guess = r.sismember(room_key + ":guesses", session['username'])
    
    if made_guess:
        return redirect('/results')
    elif 'lat' in request.args and 'lng' in request.args:
        guess = {'lat': request.args['lat'], 'lng': request.args['lng']}

        r.sadd(room_key + ":guesses", session['username'])
        r.hmset(guess_key, guess)


        if r.scard(room_key + ":guesses") == r.scard(room_key + ":players"):
            pass
            # TODO finish this for automatic reloading once guessing is done
            # socketio.emit('guessing_complete')

        return redirect('/results')
    else:
        return render_template('guess.html')

@app.route('/answer')
def answer():
    room_key = "rooms:" + session['roomName']
    is_host  = r.get(room_key + ":host").decode('utf-8') == session['username']

    if not is_host:
        return redirect('/results')
    elif 'lat' in request.args and 'lng' in request.args:
        answer = {'lat': request.args['lat'], 'lng': request.args['lng']}

        r.hmset(room_key + ":answer", answer)
        return redirect('/results')
    else:
        return render_template('guess.html', answer=True)

@app.route('/reset_room')
def reset_room():
    room_key = "rooms:" + session['roomName']
    if session['username'] != r.get(room_key + ":host").decode('utf-8'):
        return abort(403, "Only the host can clear room data")
    
    guesses = [player.decode('utf-8') for player in r.smembers(room_key + ":guesses")]
    for guess in guesses:
        r.delete(room_key + ":guesses:" + guess)
        r.srem(room_key + ":guesses", guess)

    r.delete(room_key + ":answer")

    
    return jsonify(success=True)

@app.route('/results')
def results():
    room_key = "rooms:" + session['roomName']
    is_host  = r.get(room_key + ":host").decode('utf-8') == session['username']
    made_guess = r.sismember(room_key + ":guesses", session['username'])

    if not made_guess:
        return redirect('/guess')
    elif r.exists(room_key + ":answer") and r.scard(room_key + ":guesses") == r.scard(room_key + ":players"):
        return render_template('results.html', is_host=is_host)
    elif is_host and not r.exists(room_key + ":answer"):
        return redirect('/answer')
    else:
        return render_template('waiting.html')

@app.route('/results/data')
def result_data():
    """ If the result data is ready, sends it as json """

    room_key = "rooms:" + session['roomName']
    if r.exists(room_key + ":answer") and r.scard(room_key + ":guesses") == r.scard(room_key + ":players"):
        players = [player.decode('utf-8') for player in r.smembers(room_key + ":players")]
        guesses = []
        for player in players:
            lat = float(r.hget(room_key + ":guesses:" + player, "lat"))
            lng = float(r.hget(room_key + ":guesses:" + player, "lng"))
            guess = { 'name': player, 'lat': lat, 'lng': lng }
            guesses.append(guess)

        answer_lat = float(r.hget(room_key + ":answer", "lat"))
        answer_lng = float(r.hget(room_key + ":answer", "lng"))
        answer = {'lat': answer_lat, 'lng': answer_lng}

        dists = gen_dists(guesses, answer)

        return jsonify(guesses=guesses, answer=answer, dists=dists)
    else:
        return "No Data Yet"

def gen_dists(guesses, answer):
    dists = []
    for guess in guesses:
        dist = { 'dist': latlng_dist(guess, answer), 'name': guess['name'] }
        dists.append(dist);
    
    return sorted(dists, key = lambda dist: dist['dist'])

def latlng_dist(latlng1, latlng2):
    R = 6373.0
    lat1 = math.radians(latlng1['lat'])
    lng1 = math.radians(latlng1['lng'])
    lat2 = math.radians(latlng2['lat'])
    lng2 = math.radians(latlng2['lng'])

    dlat = lng2 - lng1
    dlng = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 0.621371 # The last value converts to miles

