# utils.py
from flask_login import current_user
from werkzeug.utils import secure_filename
import os
from flask import current_app


# Helper functions
def is_super_admin():
    return current_user.is_authenticated and current_user.role == 'super_admin'

def is_agency_admin():
    return current_user.is_authenticated and current_user.role == 'agency_admin'

def save_image(image):
    filename = secure_filename(image.filename)
    filepath = os.path.join(current_app.root_path, 'static/images', filename)
    image.save(filepath)
    return filename

def delete_image(filename):
    filepath = os.path.join(current_app.root_path, 'static/images', filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def is_month_available(hotel, check_in_month):
    availability = hotel.availability.get(check_in_month)
    return availability is not None and availability > 0