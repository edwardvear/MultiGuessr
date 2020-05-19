from multiguessr import r
from flask import session
import math

def results_ready():
    roomname = session['roomname']
    answer_exists = r.exists("rooms:" + roomname + ":answer") 
    num_players = r.scard("rooms:" + roomname + ":players")
    num_guesses = r.scard("rooms:" + roomname + ":guesses")
    return answer_exists and num_players == num_guesses

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
