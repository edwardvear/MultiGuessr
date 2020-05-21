from flask import Flask
from flask_socketio import SocketIO
import redis
import os

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
socketio = SocketIO(app)
r = redis.from_url(os.environ['REDIS_URL'])

import multiguessr.routes

