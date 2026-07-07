from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from database import db
from models import Trek, Booking, RoleEnum, TrekStatusEnum, BookingStatusEnum
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
        bookings_count = Booking.query.filter_by(
            trek_id=trek.id, status=BookingStatusEnum.BOOKED
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
        
    bookings = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
    
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