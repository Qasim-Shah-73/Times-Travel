import os
import csv
import tempfile
from datetime import datetime
from io import StringIO

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, 
    Response, send_file, after_this_request, current_app
)
from flask_login import current_user, login_required

from sqlalchemy import func, case, and_
from sqlalchemy.orm import joinedload

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app import db
from app.models import Agency, User, Booking, Invoice, Guest
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

@agency_bp.route('/create_invoice', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin')
def create_invoice():
    if request.method == 'POST':
        # Process form data
        invoice_data = {
            'date': request.form.get('date', ''),
            'hcn': request.form.get('hcn', ''),
            'hotel_name': request.form.get('hotel_name', ''),
            'guest_name': request.form.get('guest_name', ''),
            'total_pax': request.form.get('total_pax', ''),
            'qty': request.form.get('qty', ''),
            'room_type': request.form.get('room_type', ''),
            'checkin': request.form.get('checkin', ''),
            'nights': request.form.get('nights', ''),
            'checkout': request.form.get('checkout', ''),
            'view': request.form.get('view', ''),
            'meal_plan': request.form.get('meal_plan', ''),
            'room_rate': request.form.get('room_rate', ''),
            'net_accommodation_charges': request.form.get('net_accommodation_charges', '0'),
            'total_net_value': request.form.get('total_net_value', '0'),
            'balance': request.form.get('balance', '0'),
            'remarks': request.form.get('remarks', ''),
            'vat': request.form.get('vat', '0'),  # Added VAT field
            'total_receipts': request.form.get('total_receipts', '0'),  # Added Total Receipts field
        }
        
        # Generate invoice
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                generate_invoice(temp_file.name, invoice_data)
                temp_file_path = temp_file.name

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(temp_file_path)
                except Exception as error:
                    current_app.logger.error(f"Error removing file {temp_file_path}: {error}")
                return response
            
            return send_file(temp_file_path, mimetype='application/pdf', as_attachment=True, download_name='invoice.pdf')
        
        except Exception as e:
            current_app.logger.error(f"Error generating invoice: {e}")
            return "Error generating invoice", 500
    
    # If it's a GET request, just render the form
    return render_template('agency/invoice_form.html')

def generate_invoice(output_filename, invoice_data):
    doc = SimpleDocTemplate(output_filename, pagesize=A4, 
                            topMargin=0.5*inch, bottomMargin=0.5*inch,
                            leftMargin=0.5*inch, rightMargin=0.5*inch)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle('Normal', fontSize=9, leading=12)
    title_style = ParagraphStyle('Title', fontSize=12, leading=14, alignment=1, spaceAfter=6)
    bold_style = ParagraphStyle('Bold', fontSize=9, leading=12, spaceBefore=6, spaceAfter=6)
    header_style = ParagraphStyle('Header', fontSize=9, leading=11, alignment=1, textColor=colors.white)

    # Add logo
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'Times_logo-high.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2.5*inch, height=1*inch)
        logo.hAlign = 'LEFT'  # Align logo to left

        # Header Section (Date, Logo, and Title)
        header_table_data = [
            [Paragraph(f"Date: {invoice_data['date']}", normal_style), 
             logo, 
             Paragraph("Definite Confirmation", title_style)]
        ]
        header_table = Table(header_table_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))

    # Guest Information Table
    guest_info_data = [
        [Paragraph("HCN #", bold_style), Paragraph(invoice_data['hcn'], normal_style),
         Paragraph("Hotel Name", bold_style), Paragraph(invoice_data['hotel_name'], normal_style)],
        [Paragraph("Guest Name", bold_style), Paragraph(invoice_data['guest_name'], normal_style),
         Paragraph("Total PAX", bold_style), Paragraph(invoice_data['total_pax'], normal_style)],
    ]
    guest_info_table = Table(guest_info_data, colWidths=[2*cm, 7*cm, 2*cm, 7*cm])
    guest_info_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(guest_info_table)
    elements.append(Spacer(1, 0.2*inch))

    # Room Details
    room_data = [
        ['QTY', 'Room Type', 'Checkin', 'Nights', 'Checkout', 'View', 'Meal Plan', 'Room Rate'],
        [Paragraph(str(invoice_data['qty']), normal_style),
         Paragraph(invoice_data['room_type'], normal_style),
         Paragraph(invoice_data['checkin'], normal_style),
         Paragraph(str(invoice_data['nights']), normal_style),
         Paragraph(invoice_data['checkout'], normal_style),
         Paragraph(invoice_data['view'], normal_style),
         Paragraph(invoice_data['meal_plan'], normal_style),
         Paragraph(f"SAR {invoice_data['room_rate']}", normal_style)]
    ]
    room_table = Table(room_data, colWidths=[1.5*cm, 3*cm, 2.5*cm, 1.5*cm, 2.5*cm, 2*cm, 2*cm, 2*cm])
    room_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002060')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(room_table)
    elements.append(Spacer(1, 0.2*inch))

    # Financial Details
    financial_data = [
        ['Net Accommodation Charges SAR:', f"SAR {invoice_data['net_accommodation_charges']}"],
        ['VAT SAR:', f"SAR {invoice_data.get('vat', 'N/A')}"],
        ['Total Net Value SAR:', f"SAR {invoice_data['total_net_value']}"],
        ['Total Receipts SAR:', f"SAR {invoice_data.get('total_receipts', 'N/A')}"],
        ['Balance SAR:', f"SAR {invoice_data['balance']}"],
    ]
    
    financial_table = Table(financial_data, colWidths=[8*cm, 4*cm])
    financial_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 0.2*inch))

    # Remarks Section
    elements.append(Paragraph(f"Remarks: {invoice_data['remarks']}", bold_style))
    elements.append(Spacer(1, 0.1*inch))

    # Terms and Conditions in a single bordered table (with outer border only)
    terms = [
        "* We hope the reservation is in accordance with your request.",
        "* Kindly make the payment by the option date to avoid automatic release of the reservation without any prior notice.",
        "* The rates mentioned above are in Saudi Riyals.",
        "* The rates mentioned above are including 15% VAT and 5% Municipality taxes, and are non-commissionable.",
        "* Any amendment to the booking is subject to availability.",
        "* Reservation can only be secured on a 100% confirmed basis through complete payment to avoid cancellation.",
        "* Cancellation Policy - The booking is non-refundable once confirmed on a definite basis."
    ]
    terms_table_data = [[Paragraph(term, ParagraphStyle('Terms', fontSize=8, leading=10))] for term in terms]
    terms_table = Table(terms_table_data, colWidths=[7.5*inch])
    terms_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(terms_table)

    # Add a space before Bank Details and Thanks section
    elements.append(Spacer(1, 0.5*inch))

    # Bank Details (Bottom Left) and "Thanks & Regards" (Bottom Right)
    bank_details = [
        [Paragraph("Our Bank Details:", bold_style)],
        [Paragraph("Natwest bank.", normal_style)],
        [Paragraph("Title: Times travel ltd", normal_style)],
        [Paragraph("Acc #: 12333034", normal_style)],
        [Paragraph("Sort code: 603003", normal_style)],
    ]
    bank_table = Table(bank_details, colWidths=[8*cm])
    bank_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    print_date = datetime.now().strftime('%d/%m/%Y')
    thanks_data = [
        [Paragraph(f"Thanks & Regards,", normal_style)],
        [Paragraph(f"Times Travel,", normal_style)],
        [Paragraph(f"Reservation", normal_style)],
        [Paragraph(f"Print Date: {print_date}", normal_style)],
    ]
    thanks_table = Table(thanks_data, colWidths=[8*cm])
    thanks_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))

    # Positioning both at the bottom: one left and one right
    footer_table = Table([[bank_table, thanks_table]], colWidths=[8*cm, 8*cm])
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)