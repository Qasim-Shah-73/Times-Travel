from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Hotel, Room
from app.forms import LoginForm, RegistrationForm, HotelForm, RoomForm, UpdateHotelForm

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
            availability=availability
        )
        db.session.add(new_hotel)
        db.session.commit()
        return redirect(url_for('main.view_hotels'))
    return render_template('create_hotel.html', form=form)

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

@bp.route('/hotels/<int:hotel_id>/update', methods=['GET', 'POST'])
@login_required
def update_hotel(hotel_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    form = UpdateHotelForm(obj=hotel)
    if form.validate_on_submit():
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

@bp.route('/hotels/<int:hotel_id>/rooms/create', methods=['GET', 'POST'])
@login_required
def create_room(hotel_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    form = RoomForm(hotel_id=hotel_id)  # Pass hotel_id to the form
    if form.validate_on_submit():
        weekend_rates_addition = {
            'January': form.weekend_rates_addition.January.data or 0,
            'February': form.weekend_rates_addition.February.data or 0,
            'March': form.weekend_rates_addition.March.data or 0,
            'April': form.weekend_rates_addition.April.data or 0,
            'May': form.weekend_rates_addition.May.data or 0,
            'June': form.weekend_rates_addition.June.data or 0,
            'July': form.weekend_rates_addition.July.data or 0,
            'August': form.weekend_rates_addition.August.data or 0,
            'September': form.weekend_rates_addition.September.data or 0,
            'October': form.weekend_rates_addition.October.data or 0,
            'November': form.weekend_rates_addition.November.data or 0,
            'December': form.weekend_rates_addition.December.data or 0
        }
        new_room = Room(
            hotel_id=hotel_id,
            type=form.type.data,
            availability=form.availability.data,
            rooms_available=form.rooms_available.data,
            rates=form.rates.data,
            weekend_rates_addition=weekend_rates_addition
        )
        db.session.add(new_room)
        db.session.commit()
        return redirect(url_for('main.view_hotels', hotel_id=hotel_id))
    return render_template('create_room.html', form=form)

@bp.route('/hotels/<int:hotel_id>/rooms/<int:room_id>/update', methods=['GET', 'POST'])
@login_required
def update_room(hotel_id, room_id):
    if not is_logged_in_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    if form.validate_on_submit():
        # Update weekend_rates_addition
        room.weekend_rates_addition = {
            'January': form.weekend_rates_addition.January.data or room.weekend_rates_addition.get('January', 0),
            'February': form.weekend_rates_addition.February.data or room.weekend_rates_addition.get('February', 0),
            'March': form.weekend_rates_addition.March.data or room.weekend_rates_addition.get('March', 0),
            'April': form.weekend_rates_addition.April.data or room.weekend_rates_addition.get('April', 0),
            'May': form.weekend_rates_addition.May.data or room.weekend_rates_addition.get('May', 0),
            'June': form.weekend_rates_addition.June.data or room.weekend_rates_addition.get('June', 0),
            'July': form.weekend_rates_addition.July.data or room.weekend_rates_addition.get('July', 0),
            'August': form.weekend_rates_addition.August.data or room.weekend_rates_addition.get('August', 0),
            'September': form.weekend_rates_addition.September.data or room.weekend_rates_addition.get('September', 0),
            'October': form.weekend_rates_addition.October.data or room.weekend_rates_addition.get('October', 0),
            'November': form.weekend_rates_addition.November.data or room.weekend_rates_addition.get('November', 0),
            'December': form.weekend_rates_addition.December.data or room.weekend_rates_addition.get('December', 0)
        }

        # Update rates
        room.rates = {
            'January': form.rates.January.data or room.rates.get('January', 0),
            'February': form.rates.February.data or room.rates.get('February', 0),
            'March': form.rates.March.data or room.rates.get('March', 0),
            'April': form.rates.April.data or room.rates.get('April', 0),
            'May': form.rates.May.data or room.rates.get('May', 0),
            'June': form.rates.June.data or room.rates.get('June', 0),
            'July': form.rates.July.data or room.rates.get('July', 0),
            'August': form.rates.August.data or room.rates.get('August', 0),
            'September': form.rates.September.data or room.rates.get('September', 0),
            'October': form.rates.October.data or room.rates.get('October', 0),
            'November': form.rates.November.data or room.rates.get('November', 0),
            'December': form.rates.December.data or room.rates.get('December', 0)
        }

        room.type = form.type.data
        room.availability = form.availability.data
        room.rooms_available = form.rooms_available.data
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

