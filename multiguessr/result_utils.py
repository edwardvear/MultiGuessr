from multiguessr import r
from flask import session
from geopy.distance import geodesic

def results_ready():
    roomname = session['roomname']
    answer_exists = r.exists("rooms:" + roomname + ":answer") 
    num_players = r.scard("rooms:" + roomname + ":players")
    num_guesses = r.scard("rooms:" + roomname + ":guesses")
    return answer_exists and num_players == num_guesses

def gen_dists(guesses, answer):
    answer_latlng = (answer['lat'], answer['lng'])

    dists = []
    for guess in guesses:
        guess_latlng = (guess['lat'], guess['lng'])
        dist = { 'dist': geodesic(guess_latlng, answer_latlng).miles, 'name': guess['name'] }
        dists.append(dist);
    
    return sorted(dists, key = lambda dist: dist['dist'])

