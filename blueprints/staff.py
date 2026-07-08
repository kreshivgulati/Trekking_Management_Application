from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from database import db
from models import User, Trek, Booking, RoleEnum, TrekStatusEnum, BookingStatusEnum, UserStatusEnum
from decorators import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@role_required(RoleEnum.STAFF)
def dashboard():
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=current_user.id
    ).all()
    
    # Calculate bookings count per trek
    treks_data = []
    for trek in assigned_treks:
        bookings_count = Booking.query.join(User).filter(
            Booking.trek_id == trek.id,
            Booking.status == BookingStatusEnum.BOOKED,
            User.status != UserStatusEnum.BLACKLISTED
        ).count()
        treks_data.append({
            "trek": trek,
            "bookings_count": bookings_count
        })
        
    return render_template(
        "staff/dashboard.html",
        treks_data=treks_data,
        statuses=TrekStatusEnum
    )


@staff_bp.route("/treks/<int:trek_id>/participants", methods=["GET"])
@login_required
@role_required(RoleEnum.STAFF)
def view_participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    
    # Security check: Ensure this trek is assigned to the current staff
    if trek.assigned_staff_id != current_user.id:
        abort(403)
        
    bookings = Booking.query.join(User).filter(
        Booking.trek_id == trek.id,
        Booking.status.in_([BookingStatusEnum.BOOKED, BookingStatusEnum.COMPLETED]),
        User.status != UserStatusEnum.BLACKLISTED
    ).order_by(Booking.booking_date.desc()).all()
    
    return render_template(
        "staff/participants.html",
        trek=trek,
        bookings=bookings
    )


@staff_bp.route("/treks/<int:trek_id>/edit", methods=["POST"])
@login_required
@role_required(RoleEnum.STAFF)
def edit_trek_details(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    
    # Security check: Ensure this trek is assigned to the current staff
    if trek.assigned_staff_id != current_user.id:
        abort(403)
        
    status_val = request.form.get("status", "")
    available_slots_val = request.form.get("available_slots", "")
    
    if not status_val or not available_slots_val:
        flash("All fields are required.", "danger")
        return redirect(url_for("staff.dashboard"))
        
    try:
        status = TrekStatusEnum(status_val)
        available_slots = int(available_slots_val)
        
        if available_slots < 0:
            flash("Available slots cannot be negative.", "danger")
            return redirect(url_for("staff.dashboard"))
            
        active_bookings_count = Booking.query.filter_by(
            trek_id=trek.id, status=BookingStatusEnum.BOOKED
        ).count()
        
        trek.available_slots = available_slots
        trek.total_slots = available_slots + active_bookings_count
        
        # update status and auto-complete bookings if COMPLETED
        trek.update_status(status)
        
        db.session.commit()
        flash(f"Trek details for '{trek.name}' updated successfully.", "success")
    except ValueError as e:
        flash(f"Invalid input data: {str(e)}", "danger")
        
    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required(RoleEnum.STAFF)
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not name or not email:
            flash("Name and Email are required fields.", "danger")
            return redirect(url_for("staff.edit_profile"))
            
        # Email uniqueness verification
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("staff.edit_profile"))
            
        current_user.name = name
        current_user.email = email
        current_user.phone = phone
        
        # If user wants to update password
        if password:
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return redirect(url_for("staff.edit_profile"))
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("staff.edit_profile"))
            current_user.set_password(password)
            
        db.session.commit()
        flash("Your profile has been updated successfully.", "success")
        return redirect(url_for("staff.dashboard"))
        
    return render_template("staff/profile.html")


@staff_bp.route("/bookings/<int:booking_id>/remove", methods=["POST"])
@login_required
@role_required(RoleEnum.STAFF)
def remove_participant(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Security check: Ensure this trek is assigned to the current staff member
    if booking.trek.assigned_staff_id != current_user.id:
        abort(403)
        
    # Check if the booking is currently active (Booked)
    if booking.status != BookingStatusEnum.BOOKED:
        flash("Only active bookings can be removed.", "danger")
        return redirect(url_for("staff.view_participants", trek_id=booking.trek_id))
        
    # Cancel the booking and restore the available slot
    booking.status = BookingStatusEnum.CANCELLED
    if booking.trek:
        booking.trek.available_slots += 1
        
    db.session.commit()
    flash(f"Trekker {booking.user.name} has been removed from the trek.", "success")
    return redirect(url_for("staff.view_participants", trek_id=booking.trek_id))