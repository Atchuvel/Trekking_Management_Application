from models.extensions import db
from datetime import date

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="Pending")

class Trek(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default="Open")
                       

class Booking(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    trek_id = db.Column(db.Integer, nullable=False)

    booking_date = db.Column(db.Date, default=date.today)

    status = db.Column(db.String(20), default="Booked")