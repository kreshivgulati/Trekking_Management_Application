from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from database import db
from models import User, Trek, Booking, RoleEnum, TrekStatusEnum, BookingStatusEnum, DifficultyEnum
from decorators import role_required

trekker_bp = Blueprint("trekker", __name__, url_prefix="/trekker")


@trekker_bp.route("/dashboard")
@login_required
@role_required(RoleEnum.TREKKER)
def dashboard():
    search_query = request.args.get("q", "").strip()
    difficulty_filter = request.args.get("difficulty", "")
    
    # Trekkers can only view approved/open treks
    query = Trek.query.filter(Trek.status.in_([TrekStatusEnum.APPROVED, TrekStatusEnum.OPEN]))
    
    if search_query:
        query = query.filter(
            (Trek.name.like(f"%{search_query}%")) |
            (Trek.location.like(f"%{search_query}%"))
        )
        
    if difficulty_filter:
        try:
            query = query.filter_by(difficulty=DifficultyEnum(difficulty_filter))
        except ValueError:
            pass
            
    open_treks = query.order_by(Trek.start_date.asc()).all()
    
    # Get user's bookings and separate into active and past
    all_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    
    active_bookings = [b for b in all_bookings if b.status == BookingStatusEnum.BOOKED]
    past_bookings = [b for b in all_bookings if b.status in (BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED)]
    
    return render_template(
        "trekker/dashboard.html",
        open_treks=open_treks,
        active_bookings=active_bookings,
        past_bookings=past_bookings,
        difficulties=DifficultyEnum,
        search_query=search_query,
        difficulty_filter=difficulty_filter
    )


@trekker_bp.route("/book/<int:trek_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.TREKKER)
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    
    # Booking conditions: trek must be  OPEN and have available slots
    if trek.status not in ( TrekStatusEnum.OPEN):
        flash("This trek is not open for bookings.", "danger")
        return redirect(url_for("trekker.dashboard"))
        
    if trek.available_slots <= 0:
        flash("Sorry, this trek is fully booked.", "danger")
        return redirect(url_for("trekker.dashboard"))
        
    # Check if they already have an active booking
    existing = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id, status=BookingStatusEnum.BOOKED
    ).first()
    if existing:
        flash("You already have an active booking for this trek.", "warning")
        return redirect(url_for("trekker.dashboard"))
        
    # Decrement available slots and save booking
    trek.available_slots -= 1
    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        status=BookingStatusEnum.BOOKED
    )
    db.session.add(booking)
    db.session.commit()
    
    flash(f"Booking confirmed for '{trek.name}'!", "success")
    return redirect(url_for("trekker.dashboard"))


@trekker_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.TREKKER)
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id:
        flash("You can only cancel your own bookings.", "danger")
        return redirect(url_for("trekker.dashboard"))
        
    if booking.status != BookingStatusEnum.BOOKED:
        flash("This booking cannot be cancelled.", "warning")
        return redirect(url_for("trekker.dashboard"))
        
    booking.status = BookingStatusEnum.CANCELLED
    booking.trek.available_slots += 1
    db.session.commit()
    
    flash(f"Booking for '{booking.trek.name}' has been cancelled.", "info")
    return redirect(url_for("trekker.dashboard"))


@trekker_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required(RoleEnum.TREKKER)
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not name or not email:
            flash("Name and Email are required fields.", "danger")
            return redirect(url_for("trekker.edit_profile"))
            
        # Email uniqueness verification
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("trekker.edit_profile"))
            
        current_user.name = name
        current_user.email = email
        current_user.phone = phone
        
        # If user wants to update password
        if password:
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return redirect(url_for("trekker.edit_profile"))
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("trekker.edit_profile"))
            current_user.set_password(password)
            
        db.session.commit()
        flash("Your profile has been updated successfully.", "success")
        return redirect(url_for("trekker.dashboard"))
        
    return render_template("trekker/profile.html")