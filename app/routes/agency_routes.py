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
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

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
        # Get the number of rooms
        qty = int(request.form.get('qty', 1))
        
        # Process base invoice data
        invoice_data = {
            'date': request.form.get('date', ''),
            'hcn': request.form.get('hcn', ''),
            'hotel_name': request.form.get('hotel_name', ''),
            'guest_name': request.form.get('guest_name', ''),
            'total_pax': request.form.get('total_pax', ''),
            'qty': qty,
            'net_accommodation_charges': request.form.get('net_accommodation_charges', '0'),
            'total_net_value': request.form.get('total_net_value', '0'),
            'balance': request.form.get('balance', '0'),
            'remarks': request.form.get('remarks', ''),
            'vat': str(float(request.form.get('total_net_value', '0')) * 0.15),  # 15% VAT
            'total_receipts': '0',
            'rooms': []
        }

        # Process each room's data
        for i in range(qty):
            room_data = {
                'room_type': request.form.get(f'room_type_{i}', ''),
                'checkin': request.form.get(f'checkin_{i}', ''),
                'nights': request.form.get(f'nights_{i}', ''),
                'checkout': request.form.get(f'checkout_{i}', ''),
                'view': request.form.get(f'view_{i}', ''),
                'meal_plan': request.form.get(f'meal_plan_{i}', ''),
                'room_rate': request.form.get(f'room_rate_{i}', '0')
            }
            invoice_data['rooms'].append(room_data)
        
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
    # Set page size and margins
    doc = SimpleDocTemplate(output_filename, pagesize=A4, 
                          topMargin=0.5*inch, bottomMargin=0.5*inch,  
                          leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements = []
    
    # Calculate available width for consistent table sizing
    available_width = doc.width
    
    # Enhanced Styles
    normal_style = ParagraphStyle(
        'Normal',
        fontSize=11,
        leading=12,
        fontName='Helvetica'
    )
    title_style = ParagraphStyle(
        'Title',
        fontSize=16,  # Increased size for Definite Booking
        leading=18,
        alignment=1,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a237e')
    )
    date_style = ParagraphStyle(
        'Date',
        fontSize=10,
        leading=12,
        fontName='Helvetica',
        textColor=colors.HexColor('#1a237e')
    )
    bold_style = ParagraphStyle(
        'Bold',
        fontSize=11,
        leading=12,
        spaceBefore=4,
        spaceAfter=4,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a237e')
    )

    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'Times_logo-high.png')
    if os.path.exists(logo_path):
        # Logo styling with stretched dimensions
        logo = Image(logo_path, width=2.2*inch, height=0.9*inch)  # Increased both width and height
        logo.hAlign = 'RIGHT'
        
        # Date styling with right alignment
        date_style = ParagraphStyle(
            'DateStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
            spaceAfter=6
        )
        
        # Title styling
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=16,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=8,
            textColor=colors.HexColor('#1a237e')
        )
        
        # Create the logo and date column (right side)
        logo_date_table = Table([
            [logo],
            [Paragraph(f"Date: {invoice_data['date']}", date_style)]
        ], colWidths=[2.4*inch])  # Increased column width to accommodate stretched logo
        
        logo_date_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, 1), 8),  # Increased space between logo and date
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # Reduced right padding to allow logo to extend
        ]))
        
        # Main header content
        header_content = [
            [
                '',  # Empty left column
                Paragraph("Definite Booking", title_style),  # Center: Title
                logo_date_table  # Right: Logo and date
            ]
        ]
        
        # Create main header table with adjusted column widths
        header_table = Table(
            header_content,
            colWidths=[
                2*inch,  # Empty left space
                available_width - 4.8*inch,  # Title width (adjusted for larger logo)
                2.8*inch  # Increased width for logo and date
            ],
            rowHeights=[1.5*inch]  # Increased height to accommodate stretched logo
        )
        
        # Apply professional styling to main header
        header_table.setStyle(TableStyle([
            # Alignment
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Title center
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),   # Logo and date right
            
            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.15*inch))

    # Rest of the styles and header definitions remain the same
    header_style = ParagraphStyle(
        'Header',
        fontSize=12,
        leading=12,
        alignment=1,
        spaceAfter=4,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )

    # Guest Information Table
    guest_info_data = [
        [Paragraph("HCN #", bold_style), Paragraph(invoice_data['hcn'], normal_style),
         Paragraph("Hotel Name", bold_style), Paragraph(invoice_data['hotel_name'], normal_style)],
        [Paragraph("Guest Name", bold_style), Paragraph(invoice_data['guest_name'], normal_style),
         Paragraph("Total PAX", bold_style), Paragraph(invoice_data['total_pax'], normal_style)],
    ]
    
    # Use available width for consistent table sizing
    guest_info_table = Table(guest_info_data, colWidths=[available_width/4]*4)
    guest_info_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e3f2fd')),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(guest_info_table)
    elements.append(Spacer(1, 0.2*inch))

    # Room Details Table with fixed column widths
    room_header = ['QTY', 'Room Type', 'Checkin', 'Nights', 'Checkout', 'View', 'Meal Plan', 'Room Rate']
    room_data = [[Paragraph(header, header_style) for header in room_header]]
    
    # Calculate proportional column widths that sum to available_width
    room_col_widths = [
        available_width * 0.10,  # QTY (6%)
        available_width * 0.10,  # Room Type (20%)
        available_width * 0.15,  # Checkin (13%)
        available_width * 0.12,  # Nights (8%)
        available_width * 0.15,  # Checkout (13%)
        available_width * 0.13,  # View (13%)
        available_width * 0.10,  # Meal Plan (13%)
        available_width * 0.14   # Room Rate (14%)
    ]
    
    for room in invoice_data['rooms']:
        room_row = [
            Paragraph("1", normal_style),
            Paragraph(room['room_type'], normal_style),
            Paragraph(room['checkin'], normal_style),
            Paragraph(str(room['nights']), normal_style),
            Paragraph(room['checkout'], normal_style),
            Paragraph(room['view'], normal_style),
            Paragraph(room['meal_plan'], normal_style),
            Paragraph(f"SAR {room['room_rate']}", normal_style)
        ]
        room_data.append(room_row)

    room_table = Table(room_data, colWidths=room_col_widths)
    room_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e3f2fd')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    elements.append(room_table)
    elements.append(Spacer(1, 0.2*inch))

    # Financial Details
    financial_data = [
        ['Net Accommodation Charges SAR:', f"SAR {invoice_data['net_accommodation_charges']}"],
        ['Balance SAR:', f"SAR {invoice_data['balance']}"],
    ]
    
    financial_table = Table(financial_data, colWidths=[available_width * 0.7, available_width * 0.3])
    financial_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e3f2fd')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#1a237e')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a237e')),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 0.2*inch))

    # Remarks Section with box
    elements.append(Paragraph("Remarks", bold_style))
    remarks_table = Table([[Paragraph(invoice_data['remarks'], normal_style)]], 
                         colWidths=[available_width])
    remarks_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e3f2fd')),
    ]))
    elements.append(remarks_table)
    elements.append(Spacer(1, 0.2*inch))

    # Terms and Conditions with box
    terms = [
        "* We hope the reservation is in accordance with your request.",
        "* Kindly make the payment by the option date to avoid automatic release of the reservation without any prior notice.",
        "* The rates mentioned above are in Saudi Riyals.",
        "* The rates mentioned above are including 15% VAT and 5% Municipality taxes, and are non-commissionable.",
        "* Any amendment to the booking is subject to availability.",
        "* Reservation can only be secured on a 100% confirmed basis through complete payment to avoid cancellation.",
        "* Cancellation Policy - The booking is non-refundable once confirmed on a definite basis."
    ]
    elements.append(Paragraph("Terms and Conditions", bold_style))
    terms_content = []
    for term in terms:
        terms_content.append([Paragraph(term, ParagraphStyle(
            'Terms',
            fontSize=10,
            leading=12,
            fontName='Helvetica'
        ))])
    
    terms_table = Table(terms_content, colWidths=[available_width])
    terms_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e3f2fd')),
    ]))
    elements.append(terms_table)

    # Footer section
    elements.append(Spacer(1, 0.2*inch))

    bank_details = [
        [Paragraph("Our Bank Details", bold_style)],
        [Paragraph("Natwest bank", normal_style)],
        [Paragraph("Title: Times travel ltd", normal_style)],
        [Paragraph("Acc #: 12333034", normal_style)],
        [Paragraph("Sort code: 603003", normal_style)],
    ]
    bank_table = Table(bank_details, colWidths=[available_width/2])
    bank_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))

    print_date = datetime.now().strftime('%d/%m/%Y')
    thanks_data = [
        [Paragraph("Thanks & Regards,", normal_style)],
        [Paragraph("Times Travel,", bold_style)],
        [Paragraph("Reservation", normal_style)],
        [Paragraph(f"Print Date: {print_date}", normal_style)],
    ]
    thanks_table = Table(thanks_data, colWidths=[available_width/2])
    thanks_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))

    footer_table = Table([[bank_table, thanks_table]], 
                        colWidths=[available_width/2]*2)
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)