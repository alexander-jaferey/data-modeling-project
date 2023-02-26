from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
