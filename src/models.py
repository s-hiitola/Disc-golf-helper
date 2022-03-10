from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    num_holes = db.Column(db.Integer, nullable=False)
    par_total = db.Column(db.Integer, nullable=False)

    holes = db.relationship("Hole", cascade="all, delete, delete-orphan", back_populates="course", passive_deletes=True)
    rounds = db.relationship("Round", back_populates="course")

class Hole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    par = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="SET NULL"))

    course = db.relationship("Course", back_populates="holes", uselist=False)
    segments = db.relationship("RoundSegment", cascade="all, delete, delete-orphan", back_populates="hole", passive_deletes=True)

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    time = db.Column(db.DateTime, nullable=False)

    player = db.relationship("Player", back_populates="rounds", uselist=False)
    course = db.relationship("Course", back_populates="rounds", uselist=False)
    segments = db.relationship("RoundSegment",cascade="all, delete-orphan", back_populates="round")

class RoundSegment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"))
    hole_id = db.Column(db.Integer, db.ForeignKey("hole.id"))
    throws = db.Column(db.Integer, nullable=False)

    round = db.relationship("Round", back_populates="segments", uselist=False)
    hole = db.relationship("Hole", back_populates="segments", uselist=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    rounds = db.relationship("Round", back_populates="player")