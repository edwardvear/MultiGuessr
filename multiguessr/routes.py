from multiguessr import app, r, socketio
from flask import session, request, jsonify, abort
from multiguessr.views import index, join, host, game, results, Player
from multiguessr.result_utils import results_ready, gen_dists


@app.route('/', methods=['GET', 'POST'])
def root():
    """ Main endpoint """

    return index()

@app.route('/submit_guess', methods=['GET', 'POST'])
def submit_guess():
    """ Submits a guess or answer """

    player = Player(session['roomname'], session['username'])
    guess = { 'lat': request.form['lat'], 'lng': request.form['lng'] }
    if player.is_host and player.already_guessed and not r.exists("rooms:" + player.roomname + ":answer"):
        r.hmset("rooms:" + player.roomname + ":answer", guess)
        if results_ready():
            socketio.emit('results_ready', '', namespace=('/' + player.roomname))
        return jsonify(success=True)
    elif not player.already_guessed:
        r.sadd("rooms:" + player.roomname + ":guesses", player.username)
        r.hmset("rooms:" + player.roomname + ":guesses:" + player.username, guess)
        if results_ready():
            socketio.emit('results_ready', '', namespace=('/' + player.roomname))
        return jsonify(success=True)
    else:
        return abort(403, "You have already submitted a guess")

@app.route('/reset_room')
def reset_room():
    """ Allows a host to reset the guesses in their room. """

    roomname, username = (session['roomname'], session['username'])
    if username != r.get("rooms:" + roomname + ":host").decode('utf-8'):
        return abort(403, "Only the host can clear room data")
    
    players = [player.decode('utf-8') for player in r.smembers("rooms:" + roomname + ":guesses")]
    for player in players:
        r.delete("rooms:" + roomname + ":guesses:" + player)
        r.srem("rooms:" + roomname + ":guesses", player)
    r.delete("rooms:" + roomname + ":answer")
    socketio.emit('reset_room', '', namespace=('/' + roomname))
    
    return jsonify(success=True)

@app.route('/leave_room')
def leave_room():
    """ Allows a player to leave their room. If they are the host, deletes the room """

    roomname, username = (session['roomname'], session['username'])
    del session['roomname']
    del session['username']

    # Remove self from room
    if r.sismember("rooms:" + roomname + ":guesses", username):
        r.srem("rooms:" + roomname + ":guesses:", username)
        r.delete("rooms:" + roomname + ":guesses:" + username)
    r.srem("rooms:" + roomname + ":players", username)

    # If host, clear the rest of the data
    if username == r.get("rooms:" + roomname + ":host").decode('utf-8'):
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

