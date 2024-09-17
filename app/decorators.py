from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def roles_required(*roles):
    """Decorator to restrict access to routes based on user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('You need to be logged in to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('You do not have the required role to access this page.', 'danger')
                return redirect(url_for('auth.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator