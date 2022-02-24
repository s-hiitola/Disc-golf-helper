from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    num_holes = db.Column(db.Integer, nullable=False)
    par_total = db.Column(db.Integer, nullable=False)

    holes = db.relationship("Hole", back_populates="course")

class Hole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    par = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))

    course = db.relationship("Course", back_populates="holes")


class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(timezone=True), server_default=func.now())
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))

    player = db.relationship("Player", back_populates="rounds")


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    rounds = db.relationship("Round", back_populates="player")