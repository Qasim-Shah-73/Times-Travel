from flask import Blueprint

def register_blueprints(app):
    from app.routes.auth_routes import auth_bp
    from app.routes.agency_routes import agency_bp
    from app.routes.booking_routes import booking_bp
    from app.routes.hotel_routes import hotel_bp
    from app.routes.room_routes import room_bp
    from app.routes.user_routes import user_bp
    from app.routes.vendors_routes import vendor_bp
    
    # Register blueprints here
    app.register_blueprint(auth_bp)
    app.register_blueprint(agency_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(hotel_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(vendor_bp)
    
