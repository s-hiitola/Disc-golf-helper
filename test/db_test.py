import os
import pytest
import tempfile
import time
import logging
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from src import models
from src.models import Course, Round, Hole, RoundSegment, Player

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    models.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    models.app.config["TESTING"] = True
    
    with models.app.app_context():
        models.db.create_all()
        
    yield models.db
    
    models.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _get_course(name="default", num_holes=18, par_total=55):
    return Course(
        name=name,
        num_holes = num_holes,
        par_total = par_total
    )

def _get_hole(number=1, par=3):
    return Hole(
        number = number,
        par = par
    )
    
def _get_round():
    return Round(
        time=datetime.now()
    )
    
def _get_round_segment(throws=1):
    return RoundSegment(
        throws = throws
    )

def _get_player():
    return Player(
        name = "John Smith"
    )
    
def test_create_instances(db_handle):
    """
    Tests that we can create one instance of each model and save them to the
    database using valid values for all columns. After creation, test that 
    everything can be found from database, and that all relationships have been
    saved correctly.
    """

    # Create everything
    course = _get_course()
    hole = _get_hole()
    player = _get_player()
    round = _get_round()
    round_segment = _get_round_segment()
    round.course = course
    round.player = player
    hole.course = course
    round_segment.hole = hole
    round_segment.round = round
    course.holes.append(hole)
    round.segments.append(round_segment)
    player.rounds.append(round)
    course.rounds.append(round)
    db_handle.session.add(course)
    db_handle.session.add(hole)
    db_handle.session.add(player)
    db_handle.session.add(round)
    db_handle.session.add(round_segment)
    db_handle.session.commit()
    
    # Check that everything exists
    assert Course.query.count() == 1
    assert Hole.query.count() == 1
    assert Player.query.count() == 1
    assert Round.query.count() == 1
    assert RoundSegment.query.count() == 1
    db_course = Course.query.first()
    db_hole = Hole.query.first()
    db_player = Player.query.first()
    db_round = Round.query.first()
    db_round_segment = RoundSegment.query.first()
    
    # Check all relationships (both sides)
    assert db_hole.course == db_course
    assert db_round.course == db_course
    assert db_round.player == db_player
    assert db_round_segment.round == db_round
    assert db_round_segment.hole == db_hole
    assert db_hole in db_course.holes
    assert db_round in db_course.rounds
    assert db_round in db_player.rounds
    assert db_round_segment in db_round.segments
    assert db_round_segment in db_hole.segments
    
def test_player_round_one_to_one(db_handle):
    """
    Tests that the relationship between player and round is one-to-one.
    i.e. that we cannot assign the same round cannot be played by more than one player.
    """
    
    # Create everything
    course = _get_course()
    hole = _get_hole()
    player1 = _get_player()
    player2 = _get_player()
    round = _get_round()
    round_segment = _get_round_segment()
    round.course = course
    round.player = player1
    round.player = player2
    hole.course = course
    round_segment.hole = hole
    round_segment.round = round
    course.holes.append(hole)
    round.segments.append(round_segment)
    db_handle.session.add(course)
    db_handle.session.add(hole)
    db_handle.session.add(player1)
    db_handle.session.add(player2)
    db_handle.session.add(round)
    db_handle.session.add(round_segment)
    with pytest.raises(Exception):
        db_handle.session.commit()
        
def test_hole_ondelete_course(db_handle):
    """
    Tests that holes are deleted when the course they are on are deleted
    """
    
    hole = _get_hole()
    course = _get_course()
    hole.course = course
    db_handle.session.add(hole)
    db_handle.session.commit()
    db_handle.session.delete(course)
    db_handle.session.commit()
    log.warning("{}".format(hole))
    assert hole == None

def test_round_segment_ondelete_round(db_handle):
    """
    Tests that holes thrown on a round are deleted when a round is deleted
    """
    
    round_segment = _get_round_segment()
    round = _get_round()
    round_segment.round = round
    db_handle.session.add(round_segment)
    db_handle.session.commit()
    db_handle.session.delete(round)
    db_handle.session.commit()
    
    assert round_segment == None
    
def test_course_columns(db_handle):
    """
    Tests sensor columns' restrictions. Name must be unique, and name and model
    must be mandatory.
    """

    # Name must be unique
    course_1 = _get_course(name="Meri-Toppila Disc Golf Park")
    course_2 = _get_course(name="Meri-Toppila Disc Golf Park")
    db_handle.session.add(course_1)
    db_handle.session.add(course_2)    
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    db_handle.session.rollback()
    
    # Name must exist
    course = _get_course()
    course.name = None
    db_handle.session.add(course)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()
    
    # Number of holes must exist
    course = _get_course()
    course.num_holes = None
    db_handle.session.add(course)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()

    # Par total must exist
    course = _get_course()
    course.par_total = None
    db_handle.session.add(course)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()
      
    
def test_hole_columns(db_handle):
    """
    Tests that holenumber and par must exist
    """

    hole = _get_hole()
    hole.number = None
    db_handle.session.add(hole)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()

    hole = _get_hole()
    hole.par = None
    db_handle.session.add(hole)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
def test_round_columns(db_handle):
    """
    Tests that all time only accepts datetime values
    """

    # Tests for column type
    round = _get_round()
    round.time = time.time()
    db_handle.session.add(round)
    with pytest.raises(StatementError):
        db_handle.session.commit()


def test_roundsegment_columns(db_handle):
    """
    Tests the types and restrictions of Round Segment columns. Checks that numerical
    values only accepts numbers. 
    """
    
    ### Does not work due to SQLite
    # round_segment = _get_round_segment()
    # round_segment.throws = str(round_segment.throws) + "throws"
    # log.warning("{}".format(round_segment.throws))
    # db_handle.session.add(round_segment)
    # with pytest.raises(StatementError):
    #     db_handle.session.commit()
        
    # db_handle.session.rollback()
    
    round_segment = RoundSegment()
    db_handle.session.add(round_segment)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()    

def test_player_columns(db_handle):
    """
    Tests that player name must be a string and must exist
    """

    # Does not work due to SQLite
    # player = _get_player()
    # player.name = 3.14159265
    # db_handle.session.add(player)
    # with pytest.raises(StatementError):
    #     db_handle.session.commit()
    
    # db_handle.session.rollback()

    player = _get_player()
    player.name = None
    db_handle.session.add(player)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
