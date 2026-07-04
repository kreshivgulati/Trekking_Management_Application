from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from database import db
from models import User, RoleEnum, UserStatusEnum

auth_bp = Blueprint("auth", __name__)


def _redirect_to_dashboard(user):
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    elif user.is_staff:
        return redirect(url_for("staff.dashboard"))
    else:
        return redirect(url_for("trekker.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_to_dashboard(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if user.is_blacklisted:
            flash("Your account has been blacklisted. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

        if user.is_staff and not user.is_approved:
            flash("Your staff account is pending admin approval.", "warning")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash(f"Welcome back, {user.name}!", "success")
        return _redirect_to_dashboard(user)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register/trekker", methods=["GET", "POST"])
def register_trekker():
    if current_user.is_authenticated:
        return _redirect_to_dashboard(current_user)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register_trekker"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register_trekker"))

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.register_trekker"))

        user = User(
            name=name, email=email, phone=phone,
            role=RoleEnum.TREKKER,
            status=UserStatusEnum.ACTIVE,
            is_approved=True,  # trekkers don't need approval, only staff do
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_trekker.html")


@auth_bp.route("/register/staff", methods=["GET", "POST"])
def register_staff():
    if current_user.is_authenticated:
        return _redirect_to_dashboard(current_user)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register_staff"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register_staff"))

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.register_staff"))

        user = User(
            name=name, email=email, phone=phone,
            role=RoleEnum.STAFF,
            status=UserStatusEnum.ACTIVE,
            is_approved=False,  # staff need admin approval before login works
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration submitted! You can log in once an admin approves your account.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_staff.html")