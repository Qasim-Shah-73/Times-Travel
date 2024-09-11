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
    account_limit = Column(Numeric(precision=5, scale=0), default=0)
    allowed_accounts = Column(Integer, default=0)

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
    hotel_id = Column(Integer, ForeignKey('hotel.id'), nullable=False)  # Link to Hotel
    hotel_name = Column(String(128), nullable=False)
    room_type = Column(String(128), nullable=True)
    agent_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=True)
    confirmation_number = Column(String(64), unique=True, nullable=True)
    booking_confirmed = Column(Boolean, default=False)
    invoice_paid = Column(Boolean, default=False)
    selling_price = Column(Numeric(precision=12, scale=2), nullable=True)
    buying_price = Column(Numeric(precision=12, scale=2), nullable=True)
    remarks = Column(Text, nullable=True)

    # Relationships
    agent = relationship('User', back_populates='bookings', foreign_keys=[agent_id])
    agency = relationship('Agency', back_populates='bookings', foreign_keys=[agency_id])
    guests = relationship('Guest', back_populates='booking', cascade="all, delete-orphan")
    hotel = relationship('Hotel', back_populates='bookings')  # New relationship to Hotel
    invoice = relationship('Invoice', back_populates='booking', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Booking {self.confirmation_number}>'

# Define the Guest model
class Guest(db.Model):
    __tablename__ = 'guests'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)  # Link to Booking model

    # Relationship to Booking model
    booking = relationship('Booking', back_populates='guests')

    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# Define the Hotel model
class Hotel(db.Model):
    __tablename__ = 'hotel'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    location = Column(String(100), nullable=False)
    availability = Column(db.JSON, nullable=False)
    image = Column(String(255), nullable=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=True)

    # Relationships
    rooms = relationship('Room', backref='hotel', cascade='all, delete-orphan', lazy=True)
    vendor = relationship('Vendor', back_populates='hotels', foreign_keys=[vendor_id])
    bookings = relationship('Booking', back_populates='hotel')  # New relationship to Booking

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'availability': self.availability,
            'image': self.image
        }

# Define the Invoice model
class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)  # Link to Booking
    time = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_method = Column(String(50), nullable=False)  # Use String for flexible payment methods
    remarks = Column(Text, nullable=True)
    tram_num = Column(String(10), nullable=True)

    # Relationship to Booking
    booking = relationship('Booking', back_populates='invoice')

    def __repr__(self):
        return f'<Invoice {self.id} for Booking {self.booking_id}>'

# Define the Room model
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
              
# Define the Vendor model
class Vendor(db.Model):
    __tablename__ = 'vendors'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    contact_person = Column(String(100), nullable=False)
    phone_number = Column(BigInteger, nullable=True)  # Phone number field
    bank_details = Column(String(255), nullable=True)

    # Explicit relationship to Hotel with back_populates
    hotels = relationship('Hotel', back_populates='vendor', lazy=True)

    def __repr__(self):
        return f'<Vendor {self.name}>'
    
