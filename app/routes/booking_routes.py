from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import User, Hotel, Room, Agency, Booking, Guest
from app.decorators import roles_required
from datetime import datetime, timedelta
from flask_login import current_user

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/search_hotels', methods=['GET'])
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

    return render_template('booking/search_hotels.html', 
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

@booking_bp.route('/booking/<int:hotel_id>/<int:room_id>', methods=['GET'])
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
            return redirect(url_for('auth.index'))
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



    return render_template('booking/booking_form.html', hotel=hotel, room=room, booking=new_booking,
                           nights=nights, persons=persons, hotel_name=hotel.name)

#booking is created here
@booking_bp.route('/book/<int:hotel_id>/<int:room_id>/<int:booking_id>', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.index'))
        
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
        return redirect(url_for('auth.index'))

    # If GET request, render the booking form
    return redirect(url_for('auth.index'))

@booking_bp.route('/bookings', methods=['GET', 'POST'])
@login_required

def view_bookings():
    return redirect(url_for('auth.index'))