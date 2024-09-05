from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

def register_blueprints(app):
    from routes.auth_routes import auth_bp
    from routes.agency_routes import agency_bp
    from routes.hotel_routes import hotel_bp
    from routes.room_routes import room_bp
    from routes.user_routes import user_bp
    from routes.booking_routes import booking_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(agency_bp)
    app.register_blueprint(hotel_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(bp)  # Register the 'main' blueprint
