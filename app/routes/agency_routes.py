from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import Agency, User
from app.forms import AgencyForm, UpdateAgencyForm
from app.decorators import roles_required
from .utils import is_super_admin, is_agency_admin

agency_bp = Blueprint('agency', __name__)

@agency_bp.route('/create_agency', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin')
def create_agency():
    if not is_super_admin():
        flash('You need to be logged in as a Super admin to access this page.', 'warning')
        return redirect(url_for('auth.index'))

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
@roles_required('super_admin', 'agency_admin')
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
@roles_required('super_admin', 'agency_admin')
def view_agencies():
    if is_super_admin():
        agencies = Agency.query.all()
    else:
        agencies = [current_user.agency]
    
    return render_template('agency/agencies.html', agencies=agencies)

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