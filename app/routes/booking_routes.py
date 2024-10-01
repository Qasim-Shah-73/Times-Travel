from flask import Blueprint, Response, render_template, redirect, url_for, flash, request, jsonify, send_file
from io import StringIO, BytesIO
import csv
from flask_login import login_required
from app import db
from app.models import User, Hotel, Room, Agency, Booking, Guest, User, Invoice, BookingRequest
from app.decorators import roles_required
from datetime import datetime, timedelta
from flask_login import current_user
from sqlalchemy import func
from decimal import Decimal
from app.email import send_tentative_email, send_confirmation_email, send_invoice_paid_email, send_invoice_email, \
                        send_tcn_confirmation_email, send_booking_reservation_status

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/search_hotels', methods=['GET'])
@login_required
def search_hotels():
    # Get user inputs
    location = request.args.get('location')
    check_in_date_str = request.args.get('check_in')
    check_out_date_str = request.args.get('check_out')
    check_in_month = datetime.strptime(check_in_date_str, '%d-%m-%Y').strftime('%B')  # Get the month name

    # Format dates to 'd-m-Y'
    check_in_date = datetime.strptime(check_in_date_str, '%d-%m-%Y')
    check_out_date = datetime.strptime(check_out_date_str, '%d-%m-%Y')

    # Initialize check-in and check-out display variables
    check_in_dt = check_in_date.strftime("%d-%m-%Y")
    check_out_dt = check_out_date.strftime("%d-%m-%Y")

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
    diff_days = (check_out_date - check_in_date).days  # Calculate the number of nights

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
            
            # Calculate total price for the room
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

            # Store the calculated total price in the room object
            room.total_price = total_price

    return render_template('booking/search_hotels.html', 
                           hotels=available_hotels, 
                           month=check_in_month, 
                           check_in=check_in_dt,
                           check_out=check_out_dt,
                           location=location,
                           nights=diff_days)

@booking_bp.route('/booking_requests', methods=['POST'])
@login_required
def booking_requests():
    try:
        # Get user inputs
        hotel_name = request.form.get('hotel_name')
        room_type = request.form.get('room_type')
        guest_name = request.form.get('guest_name', None)  # Optional field
        check_in_date = request.form.get('check_in')
        check_out_date = request.form.get('check_out')
        
        # Validate required inputs
        if not hotel_name or not room_type or not check_in_date or not check_out_date:
            flash("Missing required fields. Please fill in all required information.", "danger")
            return redirect(url_for('auth.index'))

        # Convert check-in and check-out dates to Python date objects
        check_in_date = datetime.strptime(check_in_date, '%d-%m-%Y').date()
        check_out_date = datetime.strptime(check_out_date, '%d-%m-%Y').date()

        # Create the new booking request
        new_request = BookingRequest(
            hotel_name=hotel_name,
            room_type=room_type,
            check_in=check_in_date,
            check_out=check_out_date,
            guest_name=guest_name if guest_name else 'N/A',
            agent_id = current_user.id 
        )

        # Add and commit the request to the database
        db.session.add(new_request)
        db.session.commit()

        # Log the successful booking request
        flash(f"Booking request submitted for {hotel_name} - Room: {room_type} by {current_user.username}", "success")
    except Exception as e:
        # Log the error
        flash(f"Error while submitting booking request: {e}")
        db.session.rollback()
        flash("An error occurred while processing your request. Please try again.", "danger")
    
    return redirect(url_for('auth.index'))

@booking_bp.route('/view_booking_requests', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin')
def view_booking_requests():
    requests = BookingRequest.query.all()
    return render_template('booking/view_booking_requests.html', requests=requests)
    

@booking_bp.route('/update_reservation/<int:request_id>', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin')
def update_reservation(request_id):
    # Fetch the booking request from the database
    booking_request = BookingRequest.query.get_or_404(request_id)

    # Parse JSON data from the request body
    data = request.get_json()

    # Extract status and price from the incoming request data
    status = data.get('status')
    price = data.get('price', None) 

    # Update the booking request status and price if applicable
    if status == 'approved':
        booking_request.status = True
        send_booking_reservation_status(
                to=booking_request.agent.email,
                recipient_name=booking_request.agent.username,
                agency_name=booking_request.agent.agency.name,
                check_in=booking_request.check_in.strftime('%d-%m-%Y'),
                check_out=booking_request.check_out.strftime('%d-%m-%Y'),
                hotel_name=booking_request.hotel_name,
                room_type=booking_request.room_type,
                price=price, 
                status= booking_request.status)
    elif status == 'rejected':
        booking_request.status = False
        send_booking_reservation_status(
                to=booking_request.agent.email,
                recipient_name=booking_request.agent.username,
                agency_name=booking_request.agent.agency.name,
                check_in=booking_request.check_in.strftime('%d-%m-%Y'),
                check_out=booking_request.check_out.strftime('%d-%m-%Y'),
                hotel_name=booking_request.hotel_name,
                room_type=booking_request.room_type,
                price=price, 
                status= booking_request.status)

    # Commit changes to the database
    try:
        db.session.commit()
        flash('Status updated successfully for booking request','success')
        return jsonify({'message': f'Request {status} successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
    
    if room.availability:
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
                check_in = datetime.strptime(check_in_str, '%d-%m-%Y')  # Update to match your input format
                check_out = datetime.strptime(check_out_str, '%d-%m-%Y')  # Update to match your input format
                print(f"Parsed check_in: {check_in}")
                print(f"Parsed check_out: {check_out}")
            else:
                flash("Check-in and check-out dates are required.", "danger")
                return redirect(url_for('auth.index'))
        except ValueError as e:
            print(f"Error parsing dates. Check-in: {check_in_str}, Check-out: {check_out_str}. Error: {e}")
            flash("Invalid date format. Please use DD-MM-YYYY.", "danger")
            return redirect(url_for('auth.index'))  # Redirect to a safe location
        
        remaining = agency.credit_limit - agency.used_credit + agency.paid_back
        price = Decimal(price)
        try:
            if  remaining > price:
                # Create the booking object
                new_booking = Booking(
                    check_in=check_in,
                    check_out=check_out,
                    hotel_name=hotel.name,
                    room_type=room.type,  # Updated to use `room.room_type` for consistency
                    agent_id=agent.id if agent else None,
                    agency_id=agency.id if agency else None,
                    hotel_id=hotel.id, #link hotel with booking
                    room_id=room.id,
                    booking_confirmed=False,  # Default as not confirmed
                    invoice_paid=False,  # Default as not paid
                    selling_price=price,  # Selling price from request
                    buying_price=None,  # Set if you have a buying price (could be calculated separately)
                    remarks=f"Booking created by {agent.username}."
                )
                
                agency.used_credit += price


                # Add the new booking to the session and commit
                db.session.add(new_booking)
                db.session.commit()
                
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
            else:
                flash("You have exceeded your credit limit. Contact Support Team for further queries.", "danger")
                return redirect(url_for('auth.index'))
        except ValueError as e:
            flash("You have exceeded your credit limit. Contact Support Team for further queries.", "danger")
            return redirect(url_for('auth.index'))  

#booking is created here
@booking_bp.route('/book/<int:room_id>/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def book(room_id, booking_id):
    room = Room.query.get_or_404(room_id)
    booking = Booking.query.get_or_404(booking_id)    

    if request.method == 'POST':
        if 'cancel' in request.form:
            # Handle cancellation logic
            db.session.delete(booking)
            db.session.commit()
            flash("Booking cancelled", "info")
            return redirect(url_for('auth.index'))

        # Determine the number of persons based on room type
        persons = 1 if 'Single' in room.type else \
                  2 if 'Double' in room.type else \
                  3 if 'Triple' in room.type else \
                  4 if 'Quad' in room.type else 1

        
        # Handle guests
        guests = []
        for i in range(persons):
            first_name = request.form.get(f'first_name{i}', None)
            last_name = request.form.get(f'last_name{i}', None)
            email = request.form.get(f'email{i}')
            phone_number = request.form.get(f'phone_number{i}')
            if first_name and last_name:
                guest = Guest(
                    first_name=first_name,
                    last_name=last_name,
                    email = email,
                    phone_number = phone_number,
                    booking_id=booking.id
                )
                print(guest)
                guests.append(guest)
                db.session.add(guest)

        booking.special_requests = request.form.get('special_requests')
        if booking.special_requests == 'other':
            booking.special_requests = request.form.get('other_request')
        
        booking.room.rooms_available -= 1

        db.session.commit()
        
        send_tentative_email(
            to=booking.agent.email,
            recipient_name=booking.agent.username,
            agency_name=booking.agency.name,
            destination=booking.hotel.location,
            check_in=booking.check_in.strftime('%d-%m-%Y'),
            check_out=booking.check_out.strftime('%d-%m-%Y'),
            booking_ref=f'TTL_00{booking.id}',
            hotel_name=booking.hotel.name,
            agent_ref=booking.agent.id,
            hotel_address=booking.hotel.description,
            nights=(booking.check_out - booking.check_in).days,
            num_of_rooms=1,
            room_type=room.type,
            inclusion=room.inclusion,
            notes=room.notes,
            guests=guests,
            total_price=booking.selling_price
        )
        
        flash('Booking created successfully', 'success')
        return redirect(url_for('auth.index'))

    # If GET request, render the booking form
    return redirect(url_for('auth.index'))
    

################################ Booking Dashboard ################################################

def apply_filters_and_sorting(query):
    """Apply filtering, sorting, and role-based access to the query."""
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'desc' if sort_by == 'id' else 'asc')
    filter_column = request.args.get('filter_column')
    filter_value = request.args.get('filter_value')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Apply filtering
    if filter_column and filter_value:
        filters = {
            'hotel_name': Booking.hotel_name.ilike(f'%{filter_value}%'),
            'room_type': Booking.room_type.ilike(f'%{filter_value}%'),
            'agent_name': User.username.ilike(f'%{filter_value}%'),
            'agency_name': Agency.name.ilike(f'%{filter_value}%'),
            'confirmation_number': Booking.confirmation_number.ilike(f'%{filter_value}%')
        }
        if filter_column in filters:
            if filter_column in ['agent_name', 'agency_name']:
                query = query.join(User if filter_column == 'agent_name' else Agency)
            query = query.filter(filters[filter_column])

    # Apply date range filtering
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Booking.check_in >= start_date)
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Booking.check_out <= end_date)

    # Apply sorting
    sort_columns = {
        'hotel_name': Booking.hotel_name,
        'room_type': Booking.room_type,
        'selling_price': Booking.selling_price,
        'check_in': func.date(Booking.check_in),
        'check_out': func.date(Booking.check_out),
        'agent_name': User.username,
        'agency_name': Agency.name,
        'confirmation_number': Booking.confirmation_number,
        'booking_confirmed': Booking.booking_confirmed,
        'invoice_paid': Booking.invoice_paid,
        'id': Booking.id
    }
    if sort_by in sort_columns:
        sort_column = sort_columns[sort_by]
        query = query.order_by(sort_column.desc() if sort_order == 'desc' else sort_column.asc())
    else:
        query = query.order_by(Booking.id.desc())

    return query

@booking_bp.route('/bookings', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def view_bookings():
    query = Booking.query
    query = apply_filters_and_sorting(query)

    # Apply role-based filtering
    if current_user.role == 'super_admin':
        bookings = query.all()
    elif current_user.role == 'agency_admin':
        bookings = query.filter_by(agency_id=current_user.agency_id).all()
    elif current_user.role == 'admin':
        bookings = query.filter_by(invoice_paid=False).all()

    return render_template('booking/booking_dashboard.html', 
                           bookings=bookings, 
                           sort_by=request.args.get('sort_by', 'id'),
                           sort_order=request.args.get('sort_order', 'asc'),
                           filter_column=request.args.get('filter_column'),
                           filter_value=request.args.get('filter_value'),
                           start_date=request.args.get('start_date'),
                           end_date=request.args.get('end_date'))
    
@booking_bp.route('/update_confirmation', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def update_confirmation():
    booking_id = request.form.get('booking_id')
    confirmation_number = request.form.get('confirmation_number')

    if not booking_id:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    booking = Booking.query.get(booking_id)
    
    if booking:
        if not confirmation_number == 'None':
            booking.confirmation_number = confirmation_number
            booking.booking_confirmed = True
            room = booking.room
            guests = booking.guests if booking.guests else []

            send_confirmation_email(
                to=booking.agent.email,
                recipient_name=booking.agent.username,
                agency_name=booking.agency.name,
                destination=booking.hotel.location,
                check_in=booking.check_in.strftime('%d-%m-%Y'),
                check_out=booking.check_out.strftime('%d-%m-%Y'),
                booking_ref=f'TTL_00{booking.id}',
                hotel_name=booking.hotel.name,
                agent_ref=booking.agent.id,
                hotel_address=booking.hotel.description,
                nights=(booking.check_out - booking.check_in).days,
                num_of_rooms=1,
                room_type=room.type,
                inclusion=room.inclusion,
                notes=room.notes,
                guests=guests,
                total_price=booking.selling_price,
                confirmation_number= confirmation_number
            )
        
        db.session.commit()
        
        
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'Booking not found'}), 404

@booking_bp.route('/update_times_confirmation', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def update_times_confirmation():
    booking_id = request.form.get('booking_id')
    times_confirmation_number = request.form.get('times_confirmation_number')
    times_confirmed = request.form.get('times_confirmed') == 'true'
    remarks = request.form.get('remarks')
    buying_price = request.form.get('buying_price')

    if not booking_id:
        return jsonify({'status': 'error', 'message': 'Booking ID is required'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'status': 'error', 'message': 'Booking not found'}), 404

    # Update times confirmation based on whether it's confirmed or not
    booking.times_confirmed = times_confirmed
    if times_confirmed:
        if not times_confirmation_number:
            return jsonify({'status': 'error', 'message': 'Confirmation number is required'}), 400
        booking.times_con_number = times_confirmation_number
    else:
        booking.times_con_number = None
        booking.remarks = remarks

    if buying_price:
            booking.buying_price = buying_price
            
    room = booking.room
    guests = booking.guests if booking.guests else []
    
    send_tcn_confirmation_email(
                to=booking.agent.email,
                recipient_name=booking.agent.username,
                agency_name=booking.agency.name,
                destination=booking.hotel.location,
                check_in=booking.check_in.strftime('%d-%m-%Y'),
                check_out=booking.check_out.strftime('%d-%m-%Y'),
                booking_ref=f'TTL_00{booking.id}',
                hotel_name=booking.hotel.name,
                agent_ref=booking.agent.id,
                hotel_address=booking.hotel.description,
                nights=(booking.check_out - booking.check_in).days,
                num_of_rooms=1,
                room_type=room.type,
                inclusion=room.inclusion,
                notes=room.notes,
                guests=guests,
                total_price=booking.selling_price,
                confirmation_number= times_confirmation_number
            )
    
    send_invoice_email(
                to=booking.agent.email,
                recipient_name=booking.agent.username,
                agency_name=booking.agency.name,
                destination=booking.hotel.location,
                check_in=booking.check_in.strftime('%d-%m-%Y'),
                check_out=booking.check_out.strftime('%d-%m-%Y'),
                booking_ref=f'TTL_00{booking.id}',
                hotel_name=booking.hotel.name,
                agent_ref=booking.agent.id,
                hotel_address=booking.hotel.description,
                nights=(booking.check_out - booking.check_in).days,
                num_of_rooms=1,
                room_type=room.type,
                inclusion=room.inclusion,
                notes=room.notes,
                guests=booking.guests,
                total_price=booking.selling_price                
            )

    # Commit changes to the database
    db.session.commit()

    return jsonify({'status': 'success'}), 200


@booking_bp.route('/update_invoice', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def update_invoice():
    booking_id = request.form.get('booking_id')
    payment_date_str = request.form.get('payment_date')
    payment_method = request.form.get('payment_method')
    tram_num = request.form.get('tram_num')
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
        booking.agency.paid_back += booking.selling_price
        room = booking.room
        
        # Create a new Invoice object and link it to the booking
        new_invoice = Invoice(
            booking_id=booking.id,
            time=payment_date,
            payment_method=payment_method,
            tram_num=tram_num,
            remarks=remarks
        )

        # Add the new invoice to the session
        db.session.add(new_invoice)
        db.session.commit()
        send_invoice_paid_email(
                to=booking.agent.email,
                recipient_name=booking.agent.username,
                agency_name=booking.agency.name,
                destination=booking.hotel.location,
                check_in=booking.check_in.strftime('%d-%m-%Y'),
                check_out=booking.check_out.strftime('%d-%m-%Y'),
                booking_ref=f'TTL_00{booking.id}',
                hotel_name=booking.hotel.name,
                agent_ref=booking.agent.id,
                hotel_address=booking.hotel.description,
                nights=(booking.check_out - booking.check_in).days,
                num_of_rooms=1,
                room_type=room.type,
                inclusion=room.inclusion,
                notes=room.notes,
                guests=booking.guests,
                total_price=booking.selling_price,
                invoice_id=f'TTL_00{new_invoice.id}',
                invoice_date=payment_date.strftime('%d-%m-%Y'),
                invoice_time=payment_date.strftime('%H:%M')
                
            )

        return jsonify({'status': 'success'}), 200
    
    return jsonify({'status': 'error', 'message': 'Booking not found'}), 404

@booking_bp.route('/vendor_paid', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin')
def vendor_paid():
    booking_id = request.form.get('booking_id')
    payment_number = request.form.get('payment_number')
    remarks = request.form.get('remarks')

    booking = Booking.query.get(booking_id)

    if booking:
        # Mark the booking's vendor as paid
        booking.vendor_paid = True
        booking.remarks = remarks
        booking.payment_number = payment_number

        db.session.commit()

        return jsonify({'status': 'success'}), 200
    
    return jsonify({'status': 'error', 'message': 'Booking not found'}), 404


@booking_bp.route('/get_booking_details/<int:booking_id>', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def get_booking_details(booking_id):
    print(f"Received request for booking ID: {booking_id}")  # Debugging line
    try:
        booking = Booking.query.get_or_404(booking_id)
        print(f"Booking found: {booking}")  # Debugging line
        html = render_template('booking/booking_detail.html', booking=booking)
        return jsonify({'status': 'success', 'html': html})
    except Exception as e:
        print(f"Error: {e}")  # For debugging purposes
        return jsonify({'status': 'error', 'message': 'Failed to fetch booking details.'}), 500

@booking_bp.route('/download_booking_details/<int:booking_id>', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def download_booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Create a CSV file in memory using StringIO
    output = StringIO()
    writer = csv.writer(output)

    # Write the headers
    writer.writerow(['Field', 'Value'])

    # Write the booking details
    writer.writerow(['Booking ID', booking.id])
    writer.writerow(['Agency', booking.agency.name if booking.agency else 'N/A'])
    writer.writerow(['Hotel Name', booking.hotel_name])
    writer.writerow(['Check-In', booking.check_in.strftime('%d-%m-%Y')])
    writer.writerow(['Check-Out', booking.check_out.strftime('%d-%m-%Y')])
    writer.writerow(['Room Type', booking.room_type or 'N/A'])
    writer.writerow(['Selling Price', booking.selling_price])
    writer.writerow(['Buying Price', booking.buying_price])
    writer.writerow(['Special Requests', booking.special_requests])
    writer.writerow(['Vendor', booking.hotel.vendor.name or 'N/A'])
    writer.writerow(['Agent', booking.agent.username if booking.agent else 'N/A'])
    writer.writerow(['Confirmation Number', booking.confirmation_number or 'N/A'])
    writer.writerow(['Times Confirmation Number', booking.times_con_number or 'N/A'])
    writer.writerow(['Booking Confirmed', 'Yes' if booking.booking_confirmed else 'No'])
    writer.writerow(['Invoice Paid', 'Yes' if booking.invoice_paid else 'No'])

    # Add guest information
    for i, guest in enumerate(booking.guests, 1):
        writer.writerow([f'Guest {i} Name', f'{guest.first_name} {guest.last_name}'])

    # Get CSV content as a string
    csv_content = output.getvalue()
    output.close()

    # Convert the CSV string to bytes using BytesIO
    byte_stream = BytesIO(csv_content.encode('utf-8'))
    
    # Send the file using send_file with BytesIO
    return send_file(
        byte_stream,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'booking_details_{booking_id}.csv'
    )
   
@booking_bp.route('/export_bookings', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def export_bookings():
    query = Booking.query
    query = apply_filters_and_sorting(query)

    # Apply role-based filtering
    if current_user.role == 'super_admin':
        bookings = query.all()
    elif current_user.role == 'agency_admin':
        bookings = query.filter_by(agency_id=current_user.agency_id).all()
    elif current_user.role == 'admin':
        bookings = query.filter_by(invoice_paid=False).all()

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Hotel Name', 'Room Type', 'Check-In Date', 'Check-Out Date', 'Selling Price', 'Buying Price', 'Vendor', 'Agent Name','Times Confirmation Number', 'Confirmation Number', 'Booking Confirmed', 'Invoice Paid'])

    for booking in bookings:
        writer.writerow([
            booking.id,
            booking.hotel_name,
            booking.room_type or 'N/A',
            booking.check_in.strftime('%d-%m-%Y'),
            booking.check_out.strftime('%d-%m-%Y'),
            booking.selling_price,
            booking.buying_price,
            booking.hotel.vendor.name if booking.hotel and booking.hotel.vendor else 'N/A',
            booking.agent.username if booking.agent else 'N/A',
            booking.times_con_number or 'N/A',
            booking.confirmation_number or 'N/A',
            'Yes' if booking.booking_confirmed else 'No',
            'Yes' if booking.invoice_paid else 'No'
        ])

    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=bookings.csv"})