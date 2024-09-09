from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app import db
from app.models import User, Hotel, Room, Agency, Booking, Guest, User, Invoice
from app.decorators import roles_required
from datetime import datetime, timedelta
from flask_login import current_user
from sqlalchemy import func

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
        hotel_id=hotel.id, #link hotel with booking
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
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    filter_column = request.args.get('filter_column')
    filter_value = request.args.get('filter_value')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Booking.query

    # Apply filtering if specified
    if filter_column and filter_value:
        if filter_column == 'hotel_name':
            query = query.filter(Booking.hotel_name.ilike(f'%{filter_value}%'))
        elif filter_column == 'room_type':
            query = query.filter(Booking.room_type.ilike(f'%{filter_value}%'))
        elif filter_column == 'agent_name':
            query = query.join(User).filter(User.username.ilike(f'%{filter_value}%'))
        elif filter_column == 'agency_name':
            query = query.join(Agency).filter(Agency.name.ilike(f'%{filter_value}%'))
        elif filter_column == 'confirmation_number':
            query = query.filter(Booking.confirmation_number.ilike(f'%{filter_value}%'))
            
    # Apply date range filtering if specified
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Booking.check_in >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Booking.check_out <= end_date)

    # Apply sorting
    if sort_by == 'hotel_name':
        query = query.order_by(Booking.hotel_name.asc() if sort_order == 'asc' else Booking.hotel_name.desc())
    elif sort_by == 'room_type':
        query = query.order_by(Booking.room_type.asc() if sort_order == 'asc' else Booking.room_type.desc())
    elif sort_by == 'selling_price':
        query = query.order_by(Booking.selling_price.asc() if sort_order == 'asc' else Booking.selling_price.desc())
    elif sort_by == 'check_in':
        query = query.order_by(func.date(Booking.check_in).asc() if sort_order == 'asc' else func.date(Booking.check_in).desc())
    elif sort_by == 'check_out':
        query = query.order_by(func.date(Booking.check_out).asc() if sort_order == 'asc' else func.date(Booking.check_out).desc())
    elif sort_by == 'agent_name':
        query = query.join(User).order_by(User.username.asc() if sort_order == 'asc' else User.username.desc())
    elif sort_by == 'agency_name':
        query = query.join(Agency).order_by(Agency.name.asc() if sort_order == 'asc' else Agency.name.desc())
    elif sort_by == 'confirmation_number':
        query = query.order_by(Booking.confirmation_number.asc() if sort_order == 'asc' else Booking.confirmation_number.desc())
    elif sort_by == 'booking_confirmed':
        query = query.order_by(Booking.booking_confirmed.asc() if sort_order == 'asc' else Booking.booking_confirmed.desc())
    elif sort_by == 'invoice_paid':
        query = query.order_by(Booking.invoice_paid.asc() if sort_order == 'asc' else Booking.invoice_paid.desc())
    else:
        query = query.order_by(Booking.id.asc() if sort_order == 'asc' else Booking.id.desc())

    # Apply role-based filtering
    if current_user.role == 'super_admin':
        # Super admins see all bookings
        bookings = query.all()
    elif current_user.role == 'agency_admin':
        # Agency admins see only bookings of their agency
        bookings = query.filter_by(agency_id=current_user.agency_id).all()
    elif current_user.role == 'admin':
        # Admins see only bookings where invoice_paid is False
        bookings = query.filter_by(invoice_paid=False).all()

    return render_template('booking/booking_dashboard.html', 
                           bookings=bookings, 
                           sort_by=sort_by, 
                           sort_order=sort_order, 
                           filter_column=filter_column, 
                           filter_value=filter_value,
                           start_date=start_date,
                           end_date=end_date)

@booking_bp.route('/update_confirmation', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def update_confirmation():
    booking_id = request.form.get('booking_id')
    confirmation_number = request.form.get('confirmation_number')
    buying_price = request.form.get('buying_price')

    if not booking_id or not confirmation_number or not buying_price:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    booking = Booking.query.get(booking_id)
    if booking:
        booking.confirmation_number = confirmation_number
        booking.buying_price = buying_price
        booking.booking_confirmed = True
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'Booking not found'}), 404


@booking_bp.route('/update_invoice', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def update_invoice():
    booking_id = request.form.get('booking_id')
    payment_date_str = request.form.get('payment_date')
    payment_method = request.form.get('payment_method')
    remarks = request.form.get('remarks')

    # Validate the received data
    if not booking_id or not payment_date_str or not payment_method:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    booking = Booking.query.get(booking_id)

    # Parse the payment date
    try:
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%dT%H:%M')
    except ValueError as e:
        print(f"Error parsing date: {payment_date_str}. Error: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid date format.'}), 400

    if booking:
        # Mark the booking's invoice as paid
        booking.invoice_paid = True
        
        # Create a new Invoice object and link it to the booking
        new_invoice = Invoice(
            booking_id=booking.id,
            time=payment_date,
            payment_method=payment_method,
            remarks=remarks
        )

        # Add the new invoice to the session
        db.session.add(new_invoice)
        db.session.commit()

        return jsonify({'status': 'success'}), 200
    
    return jsonify({'status': 'error', 'message': 'Booking not found'}), 404
