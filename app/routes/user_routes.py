from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import User, Agency
from app.forms import UserCreateForm, UserUpdateForm
from app.decorators import roles_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@roles_required('super_admin', 'agency_admin')
def create_user():
    agency_id = request.args.get('agency_id', type=int)
    form = UserCreateForm()

    if current_user.role == 'super_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('admin', 'Admin'), ('sub_agent', 'Sub Agent')]
    elif current_user.role == 'agency_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('sub_agent', 'Sub Agent')]
    
    if agency_id:
        form.agency_id.data = agency_id

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )

        if form.password.data:
            user.set_password(form.password.data)

        if agency_id:
            agency = Agency.query.get_or_404(agency_id)
            user.agency_id = agency.id

        db.session.add(user)
        db.session.commit()

        flash('User created successfully and assigned to the agency!', 'success')
        return redirect(url_for('user.view_all_users', agency_id=agency_id))

    return render_template('users/create_user.html', title='Create User', form=form, agency_id=agency_id)

@user_bp.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    form = UserUpdateForm(obj=user)

    # Determine the current user's role and set the choices accordingly
    if current_user.role == 'super_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('admin', 'Admin'), ('sub_agent', 'Sub Agent')]
    elif current_user.role == 'agency_admin':
        form.role.choices = [('agency_admin', 'Agency Admin'), ('sub_agent', 'Sub Agent')]
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.set_password(form.password.data)
        user.role = form.role.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('agency.view_agencies'))

    return render_template('users/update_user.html', title='Update User', form=form, user=user)

@user_bp.route('/users/<int:agency_id>', methods=['GET'])
def view_all_users(agency_id):
    agency = Agency.query.get_or_404(agency_id)
    users = User.query.filter_by(agency_id=agency_id).all()
    return render_template('users/users.html', users=users, agency=agency)

@user_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('agency.view_agencies'))
