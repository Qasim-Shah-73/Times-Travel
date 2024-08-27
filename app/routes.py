from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Hotel, Room
from app.forms import LoginForm, RegistrationForm, HotelForm, RoomForm, UpdateHotelForm, UpdateRoomForm
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from flask import current_app


bp = Blueprint('main', __name__)

def is_logged_in_admin():
    """
    Check if the user is logged in and is an admin.
    """
    if current_user.is_authenticated and current_user.is_admin:
        return True
    return False

@bp.route('/')
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('login.html', form=form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('signup.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/index')
@login_required
def index():
    return render_template('index.html')

@bp.route('/create_hotels', methods=['GET', 'POST'])
@login_required
def create_hotel():
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    form = HotelForm()
    if form.validate_on_submit():
        # Handle image upload
        image_file = None
        if form.image.data:
            image_file = save_image(form.image.data)

        availability = {
            'January': form.availability.January.data,
            'February': form.availability.February.data,
            'March': form.availability.March.data,
            'April': form.availability.April.data,
            'May': form.availability.May.data,
            'June': form.availability.June.data,
            'July': form.availability.July.data,
            'August': form.availability.August.data,
            'September': form.availability.September.data,
            'October': form.availability.October.data,
            'November': form.availability.November.data,
            'December': form.availability.December.data
        }

        new_hotel = Hotel(
            name=form.name.data,
            description=form.description.data,
            location=form.location.data,
            availability=availability,
            image=image_file  # Save image filename in the database
        )
        db.session.add(new_hotel)
        db.session.commit()
        flash('Hotel created successfully', 'success')
        return redirect(url_for('main.view_hotels'))
    
    return render_template('create_hotel.html', form=form)

def save_image(image):
    filename = secure_filename(image.filename)
    filepath = os.path.join(current_app.root_path, 'static/images', filename)
    image.save(filepath)
    return filename


@bp.route('/hotels/<int:hotel_id>/update', methods=['GET', 'POST'])
@login_required
def update_hotel(hotel_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    form = UpdateHotelForm(obj=hotel)
    
    if form.validate_on_submit():
        # Handle image update
        if form.image.data:
            if hotel.image:  # Optionally delete the old image
                delete_image(hotel.image)
            hotel.image = save_image(form.image.data)

        hotel.name = form.name.data
        hotel.description = form.description.data
        hotel.location = form.location.data
        hotel.availability = {
            'January': form.availability.January.data,
            'February': form.availability.February.data,
            'March': form.availability.March.data,
            'April': form.availability.April.data,
            'May': form.availability.May.data,
            'June': form.availability.June.data,
            'July': form.availability.July.data,
            'August': form.availability.August.data,
            'September': form.availability.September.data,
            'October': form.availability.October.data,
            'November': form.availability.November.data,
            'December': form.availability.December.data
        }
        
        db.session.commit()
        flash('Hotel updated successfully', 'success')
        return redirect(url_for('main.view_hotels'))
    
    return render_template('update_hotel.html', form=form, hotel=hotel)

def delete_image(filename):
    filepath = os.path.join(current_app.root_path, 'static/images', filename)
    if os.path.exists(filepath):
        os.remove(filepath)


@bp.route('/hotels', methods=['GET'])
@login_required
def view_hotels():
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    hotels = Hotel.query.all()
    return render_template('hotels.html', hotels=hotels)

@bp.route('/hotels/<int:hotel_id>/delete', methods=['POST'])
@login_required
def delete_hotel(hotel_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))

    hotel = Hotel.query.get_or_404(hotel_id)
    # Delete all rooms associated with the hotel
    Room.query.filter_by(hotel_id=hotel_id).delete()
    # Delete the hotel
    db.session.delete(hotel)
    db.session.commit()
    return redirect(url_for('main.view_hotels'))


@bp.route('/hotels/<int:hotel_id>/rooms/create', methods=['GET', 'POST'])
@login_required
def create_room(hotel_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))

    form = RoomForm()
    form.hotel_id.data = hotel_id  # Set the hotel_id field with the provided value

    def set_days(form_field, days):
        while len(form_field.rates) < days:
            form_field.rates.append_entry()
        while len(form_field.rates) > days:
            form_field.rates.pop_entry()

    set_days(form.january_rates, 31)
    set_days(form.february_rates, 28)
    set_days(form.march_rates, 31)
    set_days(form.april_rates, 30)
    set_days(form.may_rates, 31)
    set_days(form.june_rates, 30)
    set_days(form.july_rates, 31)
    set_days(form.august_rates, 31)
    set_days(form.september_rates, 30)
    set_days(form.october_rates, 31)
    set_days(form.november_rates, 30)
    set_days(form.december_rates, 31)

    if form.validate_on_submit():
        # Create Room object with rate dictionaries
        new_room = Room(
            hotel_id=form.hotel_id.data,
            type=form.type.data,
            availability=form.availability.data,
            rooms_available=form.rooms_available.data,
            inclusion=form.inclusion.data,
            notes=form.notes.data,
            january_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.january_rates.rates.data)},
            february_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.february_rates.rates.data)},
            march_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.march_rates.rates.data)},
            april_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.april_rates.rates.data)},
            may_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.may_rates.rates.data)},
            june_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.june_rates.rates.data)},
            july_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.july_rates.rates.data)},
            august_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.august_rates.rates.data)},
            september_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.september_rates.rates.data)},
            october_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.october_rates.rates.data)},
            november_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.november_rates.rates.data)},
            december_rates={f'Day{i+1}': rate if rate is not None else 0 for i, rate in enumerate(form.december_rates.rates.data)}
        )
        db.session.add(new_room)
        db.session.commit()
        flash('Room created successfully', 'success')
        return redirect(url_for('main.view_hotels', hotel_id=hotel_id))

    return render_template('create_room.html', form=form)

@bp.route('/hotels/<int:hotel_id>/rooms/<int:room_id>/update', methods=['GET', 'POST'])
@login_required
def update_room(hotel_id, room_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))

    room = Room.query.get_or_404(room_id)
    form = UpdateRoomForm(obj=room)

    if request.method == 'GET':
        # Populate form with existing data
        form.hotel_id.data = room.hotel_id
        form.type.data = room.type
        form.availability.data = room.availability
        form.rooms_available.data = room.rooms_available
        form.inclusion.data = room.inclusion
        form.notes.data = room.notes

        # Populate rate fields
        for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']:
            rates = getattr(room, f'{month}_rates')
            form_field = getattr(form, f'{month}_rates')
            for i, rate in enumerate(form_field):
                rate.process_data(rates.get(f'Day{i+1}', 0))

    if request.method == 'POST':
        room.type = form.type.data
        room.availability = form.availability.data
        room.rooms_available = form.rooms_available.data
        room.inclusion = form.inclusion.data
        room.notes = form.notes.data

        for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']:
            form_field = getattr(form, f'{month}_rates')
            rates = {f'Day{i+1}': rate.data if rate.data is not None else 0 for i, rate in enumerate(form_field)}
            setattr(room, f'{month}_rates', rates)

        db.session.commit()
        flash('Room updated successfully', 'success')
        return redirect(url_for('main.view_hotels', hotel_id=hotel_id))

    return render_template('update_room.html', form=form, room=room)

@bp.route('/hotel/<int:hotel_id>/room/<int:room_id>/delete', methods=['POST'])
@login_required
def delete_room(hotel_id, room_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return redirect(url_for('main.view_hotels', hotel_id=hotel_id))

@bp.route('/hotels/<int:hotel_id>/rooms', methods=['GET'])
@login_required
def view_rooms(hotel_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('rooms.html', hotel=hotel, rooms=rooms)

@bp.route('/search_hotels', methods=['GET'])
@login_required
def search_hotels():
    # Get user inputs
    location = request.args.get('location')
    check_in_date_str = request.args.get('check_in')
    check_out_date_str = request.args.get('check_out')
    check_in_month = datetime.strptime(check_in_date_str, '%Y-%m-%d').strftime('%B')  # Get the month name

    # Format dates to 'd m y'
    check_in_date = datetime.strptime(check_in_date_str, '%Y-%m-%d').strftime('%d-%m-%Y')
    check_out_date = datetime.strptime(check_out_date_str, '%Y-%m-%d').strftime('%d-%m-%Y')

    # Determine the location type based on the presence of "Makkah" or "Madinah" in the location string
    location_type = None
    if 'Makkah' in location:
        location_type = 'Makkah'
    elif 'Madinah' in location:
        location_type = 'Madinah'

    # Query database for hotels available at the specified location
    hotels = Hotel.query.filter_by(location=location_type).all()

    # Filter available hotels based on availability for the check-in month
    available_hotels = [hotel for hotel in hotels if is_month_available(hotel, check_in_month)]

    # Calculate price for each room in available hotels
    for hotel in available_hotels:
        for room in hotel.rooms:
            # Determine number of persons based on room type
            persons = 1
            if 'Single' in room.type:
                persons = 1
            elif 'Double' in room.type:
                persons = 2
            elif 'Triple' in room.type:
                persons = 3
            elif 'Quad' in room.type:
                persons = 4
            
            # Calculate price based on check-in and check-out dates
            check_in_date = datetime.strptime(check_in_date_str, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out_date_str, '%Y-%m-%d')

            total_price = 0

            # Loop through each day and add the corresponding rate for that day
            current_date = check_in_date
            while current_date < check_out_date:
                # Get the rates for the current month
                current_month_rates = getattr(room, current_date.strftime('%B').lower() + '_rates', {})
                # Add the rate for the current day to the total price
                total_price += current_month_rates.get('Day{}'.format(current_date.day), 0)
                # Move to the next day
                current_date += timedelta(days=1)

            # Multiply total price by number of persons
            total_price *= persons

            # Store the calculated total price in the room object
            room.total_price = total_price

    return render_template('search_hotels.html', 
                           hotels=available_hotels, 
                           month=check_in_month, 
                           check_in=check_in_date,
                           check_out=check_out_date,
                           location=location,
                           nights=request.args.get('total_nights'))

def is_month_available(hotel, check_in_month):
    """
    Check if the hotel has availability for the given month.
    """
    availability = hotel.availability.get(check_in_month)
    return availability is not None and availability > 0

@bp.route('/booking/<int:hotel_id>/<int:room_id>', methods=['GET'])
@login_required
def booking_form(hotel_id, room_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    room = Room.query.get_or_404(room_id)
    location = request.args.get('location')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    nights = request.args.get('nights')
    price = request.args.get('price')
    persons = 1  # Default value

    # Determine number of persons based on room type
    if 'Single' in room.type:
        persons = 1
    elif 'Double' in room.type:
        persons = 2
    elif 'Triple' in room.type:
        persons = 3
    elif 'Quad' in room.type:
        persons = 4



    return render_template('booking_form.html', hotel=hotel, room=room, location=location,
                           check_in=check_in, check_out=check_out, nights=nights, persons=persons,
                           name=hotel.name, type=room.type, price=price)

@bp.route('/book/<int:hotel_id>/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book(hotel_id, room_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    room = Room.query.get_or_404(room_id)
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    location = request.form.get('location')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    nights = request.form.get('nights')

    # Save booking data to Google Sheet
    row = [hotel.name, room.type, first_name, last_name, location, check_in, check_out, nights]
    # sheet.append_row(row)

    return redirect(url_for('main.index'))
