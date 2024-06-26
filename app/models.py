from datetime import datetime
from app import db, login
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON
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
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, nullable=False)
    rooms_available = db.Column(db.Integer, nullable=False)
    inclusion = db.Column(db.String(100))
    january_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    february_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    march_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    april_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    may_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    june_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    july_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    august_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    september_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    october_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    november_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    december_rates = db.Column(JSON, nullable=True)  # Change JSONB to TEXT
    total_price = db.Column(db.Float, default=0)

    def __init__(self, **kwargs):
        super(Room, self).__init__(**kwargs)
        self.initialize_default_rates()

    def initialize_default_rates(self):
        self.january_rates = self.january_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}
        self.february_rates = self.february_rates or {'Day{}'.format(day): 0 for day in range(1, 29)}
        self.march_rates = self.march_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}
        self.april_rates = self.april_rates or {'Day{}'.format(day): 0 for day in range(1, 31)}
        self.may_rates = self.may_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}
        self.june_rates = self.june_rates or {'Day{}'.format(day): 0 for day in range(1, 31)}
        self.july_rates = self.july_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}
        self.august_rates = self.august_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}
        self.september_rates = self.september_rates or {'Day{}'.format(day): 0 for day in range(1, 31)}
        self.october_rates = self.october_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}
        self.november_rates = self.november_rates or {'Day{}'.format(day): 0 for day in range(1, 31)}
        self.december_rates = self.december_rates or {'Day{}'.format(day): 0 for day in range(1, 32)}

    def __repr__(self):
        return f"<Room {self.id}>"

    def to_dict(self):
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'type': self.type,
            'availability': self.availability,
            'rooms_available': self.rooms_available,
            'january_rates': self.january_rates,
            'february_rates': self.february_rates,
            'march_rates': self.march_rates,
            'april_rates': self.april_rates,
            'may_rates': self.may_rates,
            'june_rates': self.june_rates,
            'july_rates': self.july_rates,
            'august_rates': self.august_rates,
            'september_rates': self.september_rates,
            'october_rates': self.october_rates,
            'november_rates': self.november_rates,
            'december_rates': self.december_rates,
            'inclusion': self.inclusion,
            'total_price': self.total_price 
        }