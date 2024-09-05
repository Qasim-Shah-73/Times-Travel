from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Hotel, Room
from app.forms import HotelForm, UpdateHotelForm
from app.decorators import roles_required
from .utils import is_super_admin, is_agency_admin, save_image, delete_image

hotel_bp = Blueprint('hotel', __name__)

@hotel_bp.route('/create_hotels', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin')
def create_hotel():
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('auth.index'))
    
    form = HotelForm()
    if form.validate_on_submit():
        image_file = None
        if form.image.data:
            image_file = save_image(form.image.data)

        availability = {month: getattr(form.availability, month).data for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']}

        new_hotel = Hotel(
            name=form.name.data,
            description=form.description.data,
            location=form.location.data,
            availability=availability,
            image=image_file
        )
        db.session.add(new_hotel)
        db.session.commit()
        flash('Hotel created successfully', 'success')
        return redirect(url_for('hotel.view_hotels'))
    
    return render_template('hotels/create_hotel.html', form=form)

@hotel_bp.route('/hotels/<int:hotel_id>/update', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin')
def update_hotel(hotel_id):
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('auth.index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    form = UpdateHotelForm(obj=hotel)
    
    if form.validate_on_submit():
        if form.image.data:
            if hotel.image:
                delete_image(hotel.image)
            hotel.image = save_image(form.image.data)

        hotel.name = form.name.data
        hotel.description = form.description.data
        hotel.location = form.location.data
        hotel.availability = {month: getattr(form.availability, month).data for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']}
        
        db.session.commit()
        flash('Hotel updated successfully', 'success')
        return redirect(url_for('hotel.view_hotels'))
    
    return render_template('hotels/update_hotel.html', form=form, hotel=hotel)

@hotel_bp.route('/hotels', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin')
def view_hotels():
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('auth.index'))
    
    hotels = Hotel.query.all()
    return render_template('hotels/hotels.html', hotels=hotels)

@hotel_bp.route('/hotels/<int:hotel_id>/delete', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin')
def delete_hotel(hotel_id):
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('auth.index'))

    hotel = Hotel.query.get_or_404(hotel_id)
    Room.query.filter_by(hotel_id=hotel_id).delete()
    db.session.delete(hotel)
    db.session.commit()
    return redirect(url_for('hotel.view_hotels'))