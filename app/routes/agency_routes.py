from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import current_user, login_required
from io import StringIO
import csv
from app import db
from app.models import Agency, User, Booking, Invoice, Guest
from sqlalchemy import func, case, and_
from sqlalchemy.orm import joinedload
from datetime import datetime
from app.forms import AgencyForm, UpdateAgencyForm
from app.decorators import roles_required
from .utils import is_super_admin

agency_bp = Blueprint('agency', __name__)

@agency_bp.route('/create_agency', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin')
def create_agency():
    form = AgencyForm()

    if form.validate_on_submit():
        agency = Agency(
            name=form.name.data,
            email=form.email.data,
            designation=form.designation.data,
            telephone=form.telephone.data,
            credit_limit=form.credit_limit.data,
            used_credit=form.used_credit.data,
            paid_back=form.paid_back.data,
            allowed_accounts=form.allowed_accounts.data
        )

        admin_user = User(
            username=form.admin_username.data,
            email=form.admin_email.data,
            role='agency_admin',
            agency=agency
        )
        admin_user.set_password(form.admin_password.data)

        db.session.add(agency)
        db.session.add(admin_user)
        db.session.commit()

        flash('Agency and admin user created successfully!', 'success')
        return redirect(url_for('agency.view_agencies'))

    return render_template('agency/create_agency.html', title='Create Agency', form=form)

@agency_bp.route('/update_agency/<int:agency_id>', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'agency_admin', 'admin')
def update_agency(agency_id):
    agency = Agency.query.get_or_404(agency_id)

    if not (current_user.role == 'super_admin' or 
        (current_user.role == 'agency_admin' and current_user.agency_id == agency_id)):
        flash('You are not allowed to update this agency.', 'danger')
        return render_template('agency/agencies.html', agencies=[agency])

        
    form = UpdateAgencyForm(obj=agency)
    
    if form.validate_on_submit():
        agency.name = form.name.data
        agency.email = form.email.data
        agency.designation = form.designation.data
        agency.telephone = form.telephone.data
        agency.credit_limit = form.credit_limit.data
        agency.used_credit = form.used_credit.data
        agency.paid_back = form.paid_back.data
        agency.allowed_accounts = form.allowed_accounts.data

        db.session.commit()
        flash('Agency updated successfully!', 'success')
        return redirect(url_for('agency.view_agencies'))

    return render_template('agency/update_agency.html', title='Update Agency', form=form, agency=agency)

@agency_bp.route('/agencies', methods=['GET'])
@login_required
@roles_required('super_admin', 'agency_admin', 'admin')
def view_agencies():
    if is_super_admin() or current_user.role == 'admin':
        agencies = Agency.query.all()
    else:
        agencies = [current_user.agency]
    
    return render_template('agency/agencies.html', agencies=agencies)


def get_agency_booking_stats(agency_id):
    # Define the aggregation query
    query = db.session.query(
        func.count(Booking.id).label("total_bookings"),
        func.sum(case(
            (and_(Booking.booking_confirmed == False, Booking.invoice_paid == False), 1),
            else_=0
        )).label("vouchered_bookings"),
        func.sum(case(
            (Booking.booking_confirmed == True, 1),
            else_=0
        )).label("confirmed_bookings"),
        func.sum(case(
            (Booking.invoice_paid == True, 1),
            else_=0
        )).label("paid_bookings"),
    ).filter(Booking.agency_id == agency_id)

    # Execute the query and fetch results
    stats = query.one()

    return {
        "total_bookings": stats.total_bookings,
        "vouchered_bookings": stats.vouchered_bookings,
        "confirmed_bookings": stats.confirmed_bookings,
        "paid_bookings": stats.paid_bookings,
    }

@agency_bp.route('/agencies_dashboard', methods=['GET'])
@login_required
@roles_required('super_admin', 'agency_admin', 'admin')
def agencies_dashboard():
    # Check if the user is super admin and get agencies accordingly
    if is_super_admin() or current_user.role == 'admin':
        agencies = Agency.query.options(joinedload(Agency.bookings)).all()
    else:
        agencies = [current_user.agency]

    agency_data = []

    for agency in agencies:
        booking_stats = get_agency_booking_stats(agency.id)
        agency_data.append({
            "agency": agency,
            **booking_stats
        })
    
    return render_template('agency/agencies_dashboard.html', agencies=agencies, agency_data=agency_data)

@agency_bp.route('/agency_detail/<int:agency_id>', methods=['GET'])
@login_required
@roles_required('super_admin', 'agency_admin', 'admin')
def agency_detail(agency_id):
    if not agency_id:
        return redirect(url_for('auth.index'))

    # Fetch the agency
    agency = Agency.query.get_or_404(agency_id)

    # Calculate remaining credit
    remaining_credit = agency.credit_limit - agency.used_credit

    # Get filter parameters
    filter_column = request.args.get('filter_column')
    filter_value = request.args.get('filter_value')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')

    # Start with a base query
    bookings_query = Booking.query.filter(Booking.agency_id == agency_id)

    # Apply filters
    if filter_column and filter_value:
        if filter_column == 'hotel_name':
            bookings_query = bookings_query.filter(Booking.hotel_name.ilike(f'%{filter_value}%'))
        elif filter_column == 'status':
            bookings_query = bookings_query.filter(Booking.booking_confirmed == (filter_value.lower() == 'confirmed'))
        elif filter_column == 'agent_name':
            bookings_query = bookings_query.join(Booking.agent).filter(User.username.ilike(f'%{filter_value}%'))
        elif filter_column == 'check_in':
            try:
                date_value = datetime.strptime(filter_value, '%Y-%m-%d').date()
                bookings_query = bookings_query.filter(Booking.check_in == date_value)
            except ValueError:
                # Handle invalid date format
                pass
        elif filter_column == 'check_out':
            try:
                date_value = datetime.strptime(filter_value, '%Y-%m-%d').date()
                bookings_query = bookings_query.filter(Booking.check_out == date_value)
            except ValueError:
                # Handle invalid date format
                pass
        elif filter_column == 'price':
            try:
                price_value = float(filter_value)
                bookings_query = bookings_query.filter(Booking.selling_price == price_value)
            except ValueError:
                # Handle invalid price format
                pass
        elif filter_column == 'payment_method':
            bookings_query = bookings_query.join(Booking.invoice).filter(Invoice.payment_method.ilike(f'%{filter_value}%'))

    # Apply date range filter
    if start_date:
        try:
            start_date_value = datetime.strptime(start_date, '%Y-%m-%d').date()
            bookings_query = bookings_query.filter(Booking.check_in >= start_date_value)
        except ValueError:
            # Handle invalid date format
            pass
    if end_date:
        try:
            end_date_value = datetime.strptime(end_date, '%Y-%m-%d').date()
            bookings_query = bookings_query.filter(Booking.check_out <= end_date_value)
        except ValueError:
            # Handle invalid date format
            pass

    # Apply sorting
    if sort_by == 'agency_id':
        bookings_query = bookings_query.order_by(Booking.id.asc() if sort_order == 'asc' else Booking.id.desc())
    elif sort_by == 'agent_name':
        bookings_query = bookings_query.join(Booking.agent).order_by(User.username.asc() if sort_order == 'asc' else User.username.desc())
    elif sort_by == 'check_in':
        bookings_query = bookings_query.order_by(Booking.check_in.asc() if sort_order == 'asc' else Booking.check_in.desc())
    elif sort_by == 'check_out':
        bookings_query = bookings_query.order_by(Booking.check_out.asc() if sort_order == 'asc' else Booking.check_out.desc())
    elif sort_by == 'hotel_name':
        bookings_query = bookings_query.order_by(Booking.hotel_name.asc() if sort_order == 'asc' else Booking.hotel_name.desc())
    elif sort_by == 'guest_name':
        bookings_query = bookings_query.join(Booking.guests).order_by(Guest.first_name.asc() if sort_order == 'asc' else Guest.first_name.desc())
    elif sort_by == 'status':
        bookings_query = bookings_query.order_by(Booking.booking_confirmed.asc() if sort_order == 'asc' else Booking.booking_confirmed.desc())
    elif sort_by == 'selling_price':
        bookings_query = bookings_query.order_by(Booking.selling_price.asc() if sort_order == 'asc' else Booking.selling_price.desc())
    elif sort_by == 'payment_method':
        bookings_query = bookings_query.join(Booking.invoice).order_by(Invoice.payment_method.asc() if sort_order == 'asc' else Invoice.payment_method.desc())

    # Execute query and prepare booking details
    bookings = bookings_query.options(
        joinedload(Booking.agent),
        joinedload(Booking.guests),
        joinedload(Booking.invoice)
    ).all()

    booking_details = []
    for booking in bookings:
        invoice = booking.invoice
        guests = booking.guests
        guest_names = ", ".join([guest.first_name for guest in guests])

        booking_details.append({
            'id': booking.id,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'hotel_name': booking.hotel_name,
            'agent_name': booking.agent.username if booking.agent else 'N/A',
            'guest_names': guest_names,
            'status': 'Confirmed' if booking.booking_confirmed else 'Pending',
            'price': f"{booking.selling_price} SAR",
            'payment_method': invoice.payment_method if invoice else 'N/A'
        })
    stats = get_agency_booking_stats(agency_id)

    # Calculate booking statistics
    total_bookings = stats['total_bookings']
    vouchered_bookings = stats['vouchered_bookings']
    confirmed_bookings = stats['confirmed_bookings']
    paid_bookings = stats['paid_bookings']

    return render_template('agency/agency_detail.html', 
                           agency=agency,
                           total_bookings=total_bookings,
                           vouchered_bookings=vouchered_bookings,
                           confirmed_bookings=confirmed_bookings,
                           paid_bookings=paid_bookings,
                           remaining_credit=remaining_credit,
                           booking_details=booking_details,
                           filter_column=filter_column,
                           filter_value=filter_value,
                           sort_by=sort_by,
                           sort_order=sort_order)
    
@agency_bp.route('/export_agencies', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin', 'agency_admin')
def export_agencies():
    agency_id = request.args.get('agency_id', type=int)
    if not agency_id:
        return "Agency ID is required", 400

    if current_user.role == 'agency_admin' and current_user.agency_id != agency_id:
        return "Unauthorized", 403

    agency = Agency.query.get_or_404(agency_id)

    # Get filter and sorting parameters
    filter_column = request.args.get('filter_column')
    filter_value = request.args.get('filter_value')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')

    # Prepare the base query
    bookings_query = Booking.query.filter(Booking.agency_id == agency_id)

    # Apply filters
    if filter_column and filter_value:
        if filter_column == 'hotel_name':
            bookings_query = bookings_query.filter(Booking.hotel_name.ilike(f'%{filter_value}%'))
        elif filter_column == 'status':
            bookings_query = bookings_query.filter(Booking.booking_confirmed == (filter_value.lower() == 'confirmed'))
        elif filter_column == 'agent_name':
            bookings_query = bookings_query.join(Booking.agent).filter(User.username.ilike(f'%{filter_value}%'))
        elif filter_column in ['check_in', 'check_out']:
            try:
                date_value = datetime.strptime(filter_value, '%Y-%m-%d').date()
                bookings_query = bookings_query.filter(getattr(Booking, filter_column) == date_value)
            except ValueError:
                pass
        elif filter_column == 'price':
            try:
                price_value = float(filter_value)
                bookings_query = bookings_query.filter(Booking.selling_price == price_value)
            except ValueError:
                pass
        elif filter_column == 'payment_method':
            bookings_query = bookings_query.join(Booking.invoice).filter(Invoice.payment_method.ilike(f'%{filter_value}%'))

    # Apply date range filter
    if start_date:
        try:
            start_date_value = datetime.strptime(start_date, '%Y-%m-%d').date()
            bookings_query = bookings_query.filter(Booking.check_in >= start_date_value)
        except ValueError:
            pass
    if end_date:
        try:
            end_date_value = datetime.strptime(end_date, '%Y-%m-%d').date()
            bookings_query = bookings_query.filter(Booking.check_out <= end_date_value)
        except ValueError:
            pass

    # Apply sorting
    sort_column = getattr(Booking, sort_by) if hasattr(Booking, sort_by) else Booking.id
    if sort_by == 'agent_name':
        sort_column = User.username
    elif sort_by == 'guest_name':
        sort_column = Guest.first_name
    elif sort_by == 'payment_method':
        sort_column = Invoice.payment_method
    
    bookings_query = bookings_query.order_by(sort_column.asc() if sort_order == 'asc' else sort_column.desc())

    # Execute query with all necessary joins
    bookings = bookings_query.options(
        joinedload(Booking.agent),
        joinedload(Booking.guests),
        joinedload(Booking.invoice)
    ).all()

    # Get agency stats
    stats = get_agency_booking_stats(agency_id)
    remaining_credit = agency.credit_limit - agency.used_credit

    # Prepare CSV
    output = StringIO()
    writer = csv.writer(output)

    # Write agency details
    writer.writerow(['Agency Details'])
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Credit Limit', 'Used Credit', 'Remaining Credit'])
    writer.writerow([
        agency.id, agency.name, agency.email, agency.telephone or 'N/A',
        agency.credit_limit, agency.used_credit, remaining_credit
    ])

    # Write booking statistics
    writer.writerow([])
    writer.writerow(['Booking Statistics'])
    writer.writerow(['Total Bookings', 'Vouchered Bookings', 'Confirmed Bookings', 'Paid Bookings'])
    writer.writerow([stats['total_bookings'], stats['vouchered_bookings'], stats['confirmed_bookings'], stats['paid_bookings']])

    # Write booking details
    writer.writerow([])
    writer.writerow(['Booking Details'])
    writer.writerow(['ID', 'Check-In', 'Check-Out', 'Hotel Name', 'Agent Name', 'Guest Names', 'Status', 'Price', 'Payment Method'])

    for booking in bookings:
        guest_names = ", ".join([guest.first_name for guest in booking.guests])
        writer.writerow([
            booking.id,
            booking.check_in.strftime('%Y-%m-%d'),
            booking.check_out.strftime('%Y-%m-%d'),
            booking.hotel_name,
            booking.agent.username if booking.agent else 'N/A',
            guest_names,
            'Confirmed' if booking.booking_confirmed else 'Pending',
            f"{booking.selling_price} SAR",
            booking.invoice.payment_method if booking.invoice else 'N/A'
        ])

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=agency_{agency.id}_details.csv"}
    )

@agency_bp.route('/delete_agency/<int:agency_id>', methods=['POST'])
@login_required
@roles_required('super_admin', 'agency_admin')
def delete_agency(agency_id):
    agency = Agency.query.get_or_404(agency_id)
    if not (current_user.role == 'super_admin' or 
        (current_user.role == 'agency_admin' and current_user.agency_id == agency_id)):
        flash('You are not allowed to delete this agency.', 'danger')
        return redirect(url_for('agency.view_agencies'))

    db.session.delete(agency)
    db.session.commit()
    
    flash('Agency deleted successfully!', 'success')
    return redirect(url_for('agency.view_agencies'))