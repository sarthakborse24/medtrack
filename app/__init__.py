"""
MedTrack — App Factory
"""
from flask import Flask, render_template
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.patients import patients_bp
    from app.routes.doctors import doctors_bp
    from app.routes.appointments import appointments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(appointments_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/403.html"), 404  # reuse layout, update as needed

    return app
