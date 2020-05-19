from flask import Flask
import redis
import os

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
r = redis.from_url(os.environ['REDIS_URL'])

import multiguessr.routes

