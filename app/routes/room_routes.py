from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Room, Hotel
from app.forms import RoomForm, UpdateRoomForm
from app.decorators import roles_required
from .utils import is_super_admin

room_bp = Blueprint('room', __name__)

@room_bp.route('/hotels/<int:hotel_id>/rooms/create', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def create_room(hotel_id):
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
            approval = current_user.role,
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
        return redirect(url_for('hotel.view_hotels', hotel_id=hotel_id))

    return render_template('rooms/create_room.html', form=form)

@room_bp.route('/hotels/<int:hotel_id>/rooms/<int:room_id>/update', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def update_room(hotel_id, room_id):
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
        room.approval = current_user.role

        for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']:
            form_field = getattr(form, f'{month}_rates')
            rates = {f'Day{i+1}': rate.data if rate.data is not None else 0 for i, rate in enumerate(form_field)}
            setattr(room, f'{month}_rates', rates)

        db.session.commit()
        flash('Room updated successfully', 'success')
        return redirect(url_for('hotel.view_hotels', hotel_id=hotel_id))

    return render_template('rooms/update_room.html', form=form, room=room)

@room_bp.route('/hotel/<int:hotel_id>/room/<int:room_id>/delete', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin','data_entry')
def delete_room(hotel_id, room_id):
    if not is_super_admin():
        flash('You need to be logged in as an admin to access this page.', 'warning')
        return redirect(url_for('auth.index'))
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return redirect(url_for('hotel.view_hotels', hotel_id=hotel_id))

@room_bp.route('/hotels/<int:hotel_id>/rooms', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def view_rooms(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('rooms/rooms.html', hotel=hotel, rooms=rooms)