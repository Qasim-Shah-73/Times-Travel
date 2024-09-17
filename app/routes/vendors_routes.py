from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import Vendor, Hotel
from app.forms import VendorCreateForm, VendorUpdateForm
from app.decorators import roles_required

vendor_bp = Blueprint('vendor', __name__)

@vendor_bp.route('/create_vendor', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def create_vendor():
    form = VendorCreateForm()
    if form.validate_on_submit():
        vendor = Vendor(
            name=form.name.data,
            email=form.email.data,
            contact_person=form.contact_person.data,
            phone_number=form.phone_number.data,
            bank_details=form.bank_details.data
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor created successfully!', 'success')
        return redirect(url_for('vendor.view_vendors', vendor_id=vendor.id))
    return render_template('vendors/create_vendor.html', title='Create Vendor', form=form)

@vendor_bp.route('/update_vendor/<int:vendor_id>', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def update_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    form = VendorUpdateForm(obj=vendor)
    if form.validate_on_submit():
        vendor.name = form.name.data
        vendor.email = form.email.data
        vendor.contact_person = form.contact_person.data
        vendor.phone_number = form.phone_number.data
        vendor.bank_details = form.bank_details.data
        db.session.commit()
        flash('Vendor updated successfully!', 'success')
        return redirect(url_for('vendor.view_vendors', vendor_id=vendor.id))
    return render_template('vendors/update_vendor.html', title='Update Vendor', form=form, vendor=vendor)

@vendor_bp.route('/vendors', methods=['GET'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def view_vendors():
    vendors = Vendor.query.all()
    return render_template('vendors/view_vendors.html', title='View Vendors', vendors=vendors)

@vendor_bp.route('/delete_vendor/<int:vendor_id>', methods=['POST'])
@login_required
@roles_required('super_admin', 'admin', 'data_entry')
def delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    db.session.delete(vendor)
    db.session.commit()
    flash('Vendor deleted successfully!', 'success')
    return redirect(url_for('vendor.view_vendors'))