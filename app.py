from flask import Flask, render_template, request, session, redirect, jsonify, abort
import redis

import os
import math

app = Flask(__name__)
r = redis.from_url(os.environ['REDIS_URL'])
app.secret_key = os.environ['SECRET_KEY']

@app.route('/')
def root():
    return index()

def index():
    if 'roomname' in session and 'username' in session:
        if not r.sismember('rooms', session['roomname']):
            del session['roomname']
            del session['username']
            return render_template('index.html', error="That Room no longer exists!")
        else:
            player = Player(session['roomname'], session['username'])
            return game(player)
    elif all(field in request.args for field in ("username", "roomname", "host_or_join")):
        roomname, username = (request.args['roomname'], request.args['username'])
        session['roomname'] = roomname
        session['username'] = username

        if request.args['host_or_join'] == 'host':
            return host(roomname, username)
        elif request.args['host_or_join'] == 'join':
            return join(roomname, username)
    else:
        return render_template('index.html')

class Player():
    def __init__(self, roomname, username):
        self.roomname = roomname
        self.username = username
        self.is_host = r.get("rooms:" + roomname + ":host").decode('utf-8') == session['username']
        self.already_guessed = r.sismember("rooms:" + roomname + ":guesses", username)

def join(roomname, username):
    if r.sismember('rooms', roomname):
        r.sadd("rooms:" + roomname + ":players", username)
        return redirect('/')
    else:
        return render_template('index.html', error="That Room doesn't exist!")

def host(roomname, username):
    if r.sismember('rooms', roomname):
        return render_template('index.html', error="That Room already esists!")
    else:
        r.sadd("rooms", roomname)
        r.sadd("rooms:" + roomname + ":players", username)
        r.set("rooms:" + roomname + ":host", username)
        return redirect('/')

def game(player):
    if player.is_host and player.already_guessed and not r.exists("rooms:" + player.roomname + ":answer"):
        return answer(player)
    elif player.already_guessed:
        return results(player)
    elif 'lat' in request.args and 'lng' in request.args:
        guess = {'lat': request.args['lat'], 'lng': request.args['lng']}

        r.sadd("rooms:" + player.roomname + ":guesses", player.username)
        r.hmset("rooms:" + player.roomname + ":guesses:" + player.username, guess)

        num_players = r.scard("rooms:" + player.roomname + ":players")
        num_guesses = r.scard("rooms:" + player.roomname + ":guesses")
        if num_players == num_guesses:
            pass
            # TODO finish this for automatic reloading once guessing is done
            # socketio.emit('guessing_complete')

        return redirect('/')
    else:
        return render_template('game.html', is_host=player.is_host)

def answer(player):
    room_key = "rooms:" + player.roomname
    if 'lat' in request.args and 'lng' in request.args:
        answer = {'lat': request.args['lat'], 'lng': request.args['lng']}

        r.hmset(room_key + ":answer", answer)
        return results(player)
    else:
        return render_template('game.html', answer=True)

def results(player):
    if results_ready():
        return render_template('results.html', is_host=player.is_host)
    else:
        return render_template('waiting.html')

def results_ready():
    roomname = session['roomname']
    answer_exists = r.exists("rooms:" + roomname + ":answer") 
    num_players = r.scard("rooms:" + roomname + ":players")
    num_guesses = r.scard("rooms:" + roomname + ":guesses")

    return answer_exists and num_players == num_guesses

@app.route('/results/data')
def result_data():
    """ If the result data is ready, sends it as json """
    roomname = session['roomname']
    if results_ready():
        players = [player.decode('utf-8') for player in r.smembers("rooms:" + roomname + ":players")]
        guesses = []
        for player in players:
            lat = float(r.hget("rooms:" + roomname + ":guesses:" + player, "lat"))
            lng = float(r.hget("rooms:" + roomname + ":guesses:" + player, "lng"))
            guess = { 'name': player, 'lat': lat, 'lng': lng }
            guesses.append(guess)

        answer_lat = float(r.hget("rooms:" + roomname + ":answer", "lat"))
        answer_lng = float(r.hget("rooms:" + roomname + ":answer", "lng"))
        answer = {'lat': answer_lat, 'lng': answer_lng}

        dists = gen_dists(guesses, answer)
        
        return jsonify(guesses=guesses, answer=answer, dists=dists)
    else:
        return "No Data Yet"

@app.route('/reset_room')
def reset_room():
    roomname, username = (session['roomname'], session['username'])
    if username != r.get("rooms:" + roomname + ":host").decode('utf-8'):
        return abort(403, "Only the host can clear room data")
    
    players = [player.decode('utf-8') for player in r.smembers("rooms:" + roomname + ":guesses")]
    for player in players:
        r.delete("rooms:" + roomname + ":guesses:" + player)
        r.srem("rooms:" + roomname + ":guesses", player)
    r.delete("rooms:" + roomname + ":answer")
    
    return jsonify(success=True)

@app.route('/delete_room')
def delete_room():
    roomname, username = (session['roomname'], session['username'])
    if username != r.get("rooms:" + roomname + ":host").decode('utf-8'):
        return abort(403, "Only the host can clear room data")

    players = [player.decode('utf-8') for player in r.smembers("rooms:" + roomname + ":guesses")]
    for player in players:
        r.delete("rooms:" + roomname + ":guesses:" + player)
        r.srem("rooms:" + roomname + ":guesses", player)
    r.delete("rooms:" + roomname + ":players")
    r.delete("rooms:" + roomname + ":guesses")
    r.delete("rooms:" + roomname + ":answer")
    r.delete("rooms:" + roomname + ":host")
    r.srem("rooms", roomname)

    return jsonify(success=True)


def gen_dists(guesses, answer):
    dists = []
    for guess in guesses:
        dist = { 'dist': latlng_dist(guess, answer), 'name': guess['name'] }
        dists.append(dist);
    
    return sorted(dists, key = lambda dist: dist['dist'])

def latlng_dist(latlng1, latlng2):
    """ Haversine formula """

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
