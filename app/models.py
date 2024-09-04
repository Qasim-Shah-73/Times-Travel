from datetime import datetime
from app import db, login
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, BigInteger, Numeric, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON
from werkzeug.security import generate_password_hash, check_password_hash

# Define the Agency model
class Agency(db.Model):
    __tablename__ = 'agencies'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    email = Column(String(120), index=True, unique=True, nullable=False)
    designation = Column(String(128), nullable=True)
    telephone = Column(BigInteger, nullable=True)
    credit_limit = Column(Numeric(precision=12, scale=2), default=0.00)
    used_credit = Column(Numeric(precision=12, scale=2), default=0.00)
    paid_back = Column(Numeric(precision=12, scale=2), default=0.00)

    # Relationship to User model
    users = relationship(
        'User',
        back_populates='agency',
        foreign_keys='User.agency_id'
    )

    # Relationship to Booking model
    bookings = relationship(
        'Booking',
        back_populates='agency',
        foreign_keys='Booking.agency_id'
    )

    def __repr__(self):
        return f'<Agency {self.name}>'

# Define the User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False, default='user')
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=True)

    # Relationship with the Agency model
    agency = relationship(
        'Agency',
        back_populates='users',
        foreign_keys=[agency_id]
    )

    # Relationship to Booking model
    bookings = relationship(
        'Booking',
        back_populates='agent',
        foreign_keys='Booking.agent_id'
    )

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Define the Booking model
class Booking(db.Model):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    hotel_name = Column(String(128), nullable=False)
    room_type = Column(String(128), nullable=True)
    guest_details = Column(Text, nullable=True)
    agent_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Agent associated with booking
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=True)  # Agency associated with booking
    confirmation_number = Column(String(64), unique=True, nullable=False)
    booking_confirmed = Column(Boolean, default=False)
    invoice_paid = Column(Boolean, default=False)
    selling_price = Column(Numeric(precision=12, scale=2), nullable=True)
    buying_price = Column(Numeric(precision=12, scale=2), nullable=True)
    remarks = Column(Text, nullable=True)

    # Relationships
    agent = relationship('User', back_populates='bookings', foreign_keys=[agent_id])
    agency = relationship('Agency', back_populates='bookings', foreign_keys=[agency_id])

    def __repr__(self):
        return f'<Booking {self.confirmation_number}>'
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.JSON, nullable=False)  # Dictionary to hold availability for each month
    image = db.Column(db.String(255), nullable=True)  # New field to store image filename or URL
    rooms = db.relationship('Room', backref='hotel', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'availability': self.availability,
            'image': self.image  # Include image in the dict
        }


class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, nullable=False)
    rooms_available = db.Column(db.Integer, nullable=False)
    inclusion = db.Column(db.String(100))
    notes = db.Column(db.String(100))
    january_rates = db.Column(JSON, nullable=True)
    february_rates = db.Column(JSON, nullable=True)
    march_rates = db.Column(JSON, nullable=True)
    april_rates = db.Column(JSON, nullable=True)
    may_rates = db.Column(JSON, nullable=True)
    june_rates = db.Column(JSON, nullable=True)
    july_rates = db.Column(JSON, nullable=True)
    august_rates = db.Column(JSON, nullable=True)
    september_rates = db.Column(JSON, nullable=True)
    october_rates = db.Column(JSON, nullable=True)
    november_rates = db.Column(JSON, nullable=True)
    december_rates = db.Column(JSON, nullable=True)
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