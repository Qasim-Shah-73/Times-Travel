from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Hotel, Room, Agency, Booking, Guest
from app.forms import LoginForm, RegistrationForm, HotelForm, RoomForm, UpdateHotelForm, UpdateRoomForm, AgencyForm, UserUpdateForm, UpdateAgencyForm, UserCreateForm
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.decorators import roles_required

bp = Blueprint('main', __name__)

def is_super_admin():
    """
    Check if the user is logged in and is an admin.
    """
    if current_user.is_authenticated and current_user.role == 'super_admin':
        return True
    return False

def is_agency_admin():
    """
    Check if the user is logged in and is an agency admin.
    """
    if current_user.is_authenticated and current_user.role == 'agency_admin':
        return True
    return False

# Basic Index Routes and Login Signup

@bp.route('/')
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data)[0]
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

# User routes
@bp.route('/create_user', methods=['GET', 'POST'])
@roles_required('super_admin', 'agency_admin')
def create_user():
    # Retrieve agency_id from query parameters
    agency_id = request.args.get('agency_id', type=int)
    
    form = UserCreateForm()

    # Determine the current user's role and set the choices accordingly
    if current_user.role == 'super_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('admin', 'Admin'), ('sub_agent', 'Sub Agent')]
    elif current_user.role == 'agency_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('sub_agent', 'Sub Agent')]
    
    if agency_id:
        form.agency_id.data = agency_id

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )

        if form.password.data:
            user.set_password(form.password.data)

        # Assign the user to the specified agency
        if agency_id:
            agency = Agency.query.get_or_404(agency_id)
            user.agency_id = agency.id

        db.session.add(user)
        db.session.commit()

        flash('User created successfully and assigned to the agency!', 'success')
        return redirect(url_for('main.view_all_users', agency_id=agency_id))

    return render_template('create_user.html', title='Create User', form=form, agency_id=agency_id)

@bp.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    form = UserUpdateForm(obj=user)

    # Determine the current user's role and set the choices accordingly
    if current_user.role == 'super_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('admin', 'Admin'), ('sub_agent', 'Sub Agent')]
    elif current_user.role == 'agency_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('sub_agent', 'Sub Agent')]
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.set_password(form.password.data)
        user.role = form.role.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('main.view_agencies'))

    return render_template('update_user.html', title='Update User', form=form, user=user)

@bp.route('/users/<int:agency_id>', methods=['GET'])
def view_all_users(agency_id):
    agency = Agency.query.get_or_404(agency_id)
    users = User.query.filter_by(agency_id=agency_id).all()
    return render_template('users.html', users=users, agency=agency)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.view_agencies'))

# Agency Routes

@bp.route('/create_agency', methods=['GET', 'POST'])
@roles_required('super_admin')
def create_agency():
    if not is_super_admin():
        flash('You need to be logged in as a Super admin to access this page.', 'warning')
        return redirect(url_for('main.index'))

    form = AgencyForm()

    if form.validate_on_submit():
        # Create the agency
        agency = Agency(
            name=form.name.data,
            email=form.email.data,
            designation=form.designation.data,
            telephone=form.telephone.data,
            credit_limit=form.credit_limit.data,
            used_credit=form.used_credit.data,
            paid_back=form.paid_back.data
        )

        # Create the admin user for the agency
        admin_user = User(
            username=form.admin_username.data,
            email=form.admin_email.data,
            role = 'agency_admin',
            agency=agency  # Link the new admin user to this agency
        )
        admin_user.set_password(form.admin_password.data)

        # Add both the new user and agency to the session
        db.session.add(agency)
        db.session.add(admin_user)
        db.session.commit()

        flash('Agency and admin user created successfully!', 'success')
        return redirect(url_for('main.view_agencies'))

    return render_template('create_agency.html', title='Create Agency', form=form)

@bp.route('/update_agency/<int:agency_id>', methods=['GET', 'POST'])
@roles_required('super_admin', 'agency_admin')
def update_agency(agency_id):
    agency = Agency.query.get_or_404(agency_id)
    
    if not (current_user.agency_id == agency_id):
        flash('You are not allowed to update this agency.', 'danger')
        return render_template('agencies.html', agencies=agency)
        
    form = UpdateAgencyForm(obj=agency)
    
    if form.validate_on_submit():
        agency.name = form.name.data
        agency.email = form.email.data
        agency.designation = form.designation.data
        agency.telephone = form.telephone.data
        agency.credit_limit = form.credit_limit.data
        agency.used_credit = form.used_credit.data
        agency.paid_back = form.paid_back.data

        db.session.commit()
        flash('Agency updated successfully!', 'success')
        return redirect(url_for('main.view_agencies'))

    return render_template('update_agency.html', title='Update Agency', form=form, agency=agency)

@bp.route('/agencies', methods=['GET'])
@login_required
@roles_required('super_admin', 'agency_admin')
def view_agencies():
    if is_super_admin():
        agencies = Agency.query.all()
    else:
        agencies = current_user.agency
        agencies = [agencies]
    
    return render_template('agencies.html', agencies=agencies)


@bp.route('/delete_agency/<int:agency_id>', methods=['POST'])
@roles_required('super_admin', 'agency_admin')
def delete_agency(agency_id):
    agency = Agency.query.get_or_404(agency_id)
    if not (current_user.agency_id == agency_id):
        flash('You are not allowed to delete this agency.', 'danger')

    db.session.delete(agency)
    db.session.commit()
    
    flash('Agency deleted successfully!', 'success')
    return redirect(url_for('main.view_agencies'))

# Hotel Routes

@bp.route('/create_hotels', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin')
def create_hotel():
    if not is_super_admin():
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
@roles_required('super_admin', 'admin')
def update_hotel(hotel_id):
    if not is_super_admin():
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
@roles_required('super_admin', 'admin')
def view_hotels():
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    hotels = Hotel.query.all()
    return render_template('hotels.html', hotels=hotels)

@bp.route('/hotels/<int:hotel_id>/delete', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin')
def delete_hotel(hotel_id):
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))

    hotel = Hotel.query.get_or_404(hotel_id)
    # Delete all rooms associated with the hotel
    Room.query.filter_by(hotel_id=hotel_id).delete()
    # Delete the hotel
    db.session.delete(hotel)
    db.session.commit()
    return redirect(url_for('main.view_hotels'))

# Room Routes

@bp.route('/hotels/<int:hotel_id>/rooms/create', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin')
def create_room(hotel_id):
    if not is_super_admin():
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
@roles_required('super_admin', 'admin')
def update_room(hotel_id, room_id):
    if not is_super_admin():
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
@roles_required('super_admin', 'admin')
def delete_room(hotel_id, room_id):
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return redirect(url_for('main.view_hotels', hotel_id=hotel_id))

@bp.route('/hotels/<int:hotel_id>/rooms', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin')
def view_rooms(hotel_id):
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('main.index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('rooms.html', hotel=hotel, rooms=rooms)

# Front End

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
    
    # Extract query parameters
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    nights = request.args.get('nights')
    price = request.args.get('price')

    # Assuming the current user is the agent making the booking
    agent = current_user

    # Example agency fetch based on the agent's info
    agency = agent.agency if agent.agency else None
    # Convert check_in and check_out to datetime objects if they are strings
    try:
        if check_in_str and check_out_str:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d %H:%M:%S')
            print(f"Parsed check_in: {check_in}")
            print(f"Parsed check_out: {check_out}")
        else:
            flash("Check-in and check-out dates are required.", "danger")
            return redirect(url_for('some_error_handling_view'))  # Redirect to an error handling view or the booking form
    except ValueError as e:
        print(f"Error parsing dates. Check-in: {check_in_str}, Check-out: {check_out_str}. Error: {e}")
        flash("Invalid date format. Please use YYYY-MM-DD HH:MM:SS.", "danger")

    # Create the booking object
    new_booking = Booking(
        check_in=check_in,
        check_out=check_out,
        hotel_name=hotel.name,
        room_type=room.type,  # Updated to use `room.room_type` for consistency
        agent_id=agent.id if agent else None,
        agency_id=agency.id if agency else None,
        booking_confirmed=False,  # Default as not confirmed
        invoice_paid=False,  # Default as not paid
        selling_price=price,  # Selling price from request
        buying_price=None,  # Set if you have a buying price (could be calculated separately)
        remarks=f"Booking created by {agent.username}."
    )

    # Add the new booking to the session and commit
    db.session.add(new_booking)
    db.session.commit()
    
    flash('Booking created successfully', 'success')

    # Determine number of persons based on room type
    if 'Single' in room.type:
        persons = 1
    elif 'Double' in room.type:
        persons = 2
    elif 'Triple' in room.type:
        persons = 3
    elif 'Quad' in room.type:
        persons = 4



    return render_template('booking_form.html', hotel=hotel, room=room, booking=new_booking,
                           nights=nights, persons=persons, hotel_name=hotel.name)

#booking is created here
@bp.route('/book/<int:hotel_id>/<int:room_id>/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def book(hotel_id, room_id, booking_id):
    room = Room.query.get_or_404(room_id)
    booking = Room.query.get_or_404(booking_id)
    
    
    if request.method == 'POST':
        if 'cancel' in request.form:
            # Handle cancellation logic here
            db.session.delete(booking)
            db.session.commit()
            flash("Booking cancelled", "info")
            return redirect(url_for('main.index'))
        
        # Determine number of persons based on room type
        if 'Single' in room.type:
            persons = 1
        elif 'Double' in room.type:
            persons = 2
        elif 'Triple' in room.type:
            persons = 3
        elif 'Quad' in room.type:
            persons = 4


        # Handle guests
        for i in range(persons):
            first_name = request.form.get(f'first_name{i}')
            last_name = request.form.get(f'last_name{i}')
            if first_name and last_name:
                guest = Guest(
                    first_name=first_name,
                    last_name=last_name,
                    booking_id=booking.id
                )
                db.session.add(guest)

        db.session.commit()
        
        flash('Booking created successfully', 'success')
        return redirect(url_for('main.index'))

    # If GET request, render the booking form
    return redirect(url_for('main.index'))

@bp.route('/bookings', methods=['GET', 'POST'])
@login_required

def view_bookings():
    return redirect(url_for('main.index'))