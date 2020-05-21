from multiguessr import app, r
from multiguessr.result_utils import results_ready, gen_dists
from flask import Flask, render_template, request, session, redirect

class Player():
    """ A class to store user state as they are routed through the app. """

    def __init__(self, roomname, username):
        self.roomname = roomname
        self.username = username
        self.is_host = r.get("rooms:" + roomname + ":host").decode('utf-8') == session['username']
        self.already_guessed = r.sismember("rooms:" + roomname + ":guesses", username)

def index():
    """ Determines the current state of the user, and routes them to the proper place. """

    if 'roomname' in session and 'username' in session:
        if not r.sismember('rooms', session['roomname']):
            del session['roomname']
            del session['username']
            return render_template('index.html', error="That Room no longer exists!")
        else:
            player = Player(session['roomname'], session['username'])
            return game(player)
    elif all(field in request.form for field in ("username", "roomname", "host_or_join")):
        roomname, username = (request.form['roomname'], request.form['username'])
        session['roomname'] = roomname
        session['username'] = username

        if request.form['host_or_join'] == 'host':
            return host(roomname, username)
        elif request.form['host_or_join'] == 'join':
            return join(roomname, username)
    else:
        return render_template('index.html')

def join(roomname, username):
    """ Adds the given username to the room if it exists. """

    if r.sismember('rooms', roomname):
        r.sadd("rooms:" + roomname + ":players", username)
        return redirect('/')
    else:
        return render_template('index.html', error="That Room doesn't exist!")

def host(roomname, username):
    """ If the room doesn't already exists, creates it and adds the given username as host. """

    if r.sismember('rooms', roomname):
        return render_template('index.html', error="That Room already esists!")
    else:
        r.sadd("rooms", roomname)
        r.sadd("rooms:" + roomname + ":players", username)
        r.set("rooms:" + roomname + ":host", username)
        return redirect('/')

def game(player):
    """ Handles user guessing """

    if player.is_host and player.already_guessed and not r.exists("rooms:" + player.roomname + ":answer"):
        return render_template('game.html', answer=True)
    elif player.already_guessed:
        return results(player)
    else:
        return render_template('game.html', is_host=player.is_host)

def results(player):
    """ Shows either a waiting page or the results for the round """

    if results_ready():
        return render_template('results.html', is_host=player.is_host)
    else:
        return render_template('waiting.html')

