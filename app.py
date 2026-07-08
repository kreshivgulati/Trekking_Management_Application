import os
from flask import Flask, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, logout_user

from database import db
from models import User, RoleEnum, UserStatusEnum

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-change-in-prod"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'trek_management.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def check_blacklisted():
        if request.endpoint and (request.endpoint.startswith('static') or request.endpoint == 'auth.login' or request.endpoint == 'auth.logout'):
            return
        if current_user.is_authenticated and current_user.is_blacklisted:
            logout_user()
            flash("Your account has been blacklisted. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.staff import staff_bp
    from blueprints.trekker import trekker_bp
    from blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(trekker_bp)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for("admin.dashboard"))
            elif current_user.is_staff:
                return redirect(url_for("staff.dashboard"))
            else:
                return redirect(url_for("trekker.dashboard"))
        return redirect(url_for("auth.login"))

    # Create tables + seed admin here so this runs no matter how the app
    # is started: `flask run`, `python app.py`, gunicorn, etc. Putting
    # this only in `if __name__ == "__main__"` would skip it under
    # `flask run`, since that entry point only calls create_app().
    with app.app_context():
        _init_db()

    return app


def _init_db():
    """Creates all tables programmatically and seeds the one pre-existing
    admin account (spec: no admin registration allowed). Must be called
    from inside an app context."""
    db.create_all()

    admin_email = "admin@trekapp.com"
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            name="System Admin",
            email=admin_email,
            role=RoleEnum.ADMIN,
            status=UserStatusEnum.ACTIVE,
            is_approved=True,
        )
        admin.set_password("12345678")
        db.session.add(admin)
        db.session.commit()
        print(f"Seeded admin: {admin_email} / 12345678")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)