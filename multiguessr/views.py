from multiguessr import app, r
from multiguessr.result_utils import results_ready, gen_dists, latlng_dist
from flask import Flask, render_template, request, session, redirect

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