from multiguessr import app, r
from flask import session, jsonify, abort
from multiguessr.views import index, join, host, game, answer, results
from multiguessr.result_utils import results_ready, gen_dists


@app.route('/')
def root():
    return index()

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