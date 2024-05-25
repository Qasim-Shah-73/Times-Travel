from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.JSON, nullable=False)  # Dictionary to hold availability for each month
    rooms = db.relationship('Room', backref='hotel', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'availability': self.availability
        }

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, default=True)
    rooms_available = db.Column(db.Integer, default=1)
    rates = db.Column(db.JSON, nullable=False)  # Dictionary to hold rates for each month
    weekend_rates_addition = db.Column(db.JSON, default={})  # Dictionary to hold weekend rates addition for each month

    def to_dict(self):
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'type': self.type,
            'availability': self.availability,
            'rooms_available': self.rooms_available,
            'rates': self.rates,
            'weekend_rates_addition': self.weekend_rates_addition
        }